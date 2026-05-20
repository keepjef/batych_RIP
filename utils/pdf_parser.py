import hashlib
import json
import logging
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz

from llm.client import generate_from_image


_cache_lock = threading.Lock()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_cache_key(image_hash: str, vision_model: str) -> str:
    return f"{vision_model}::{image_hash}"


def _load_cache(cache_file: Path) -> dict:
    if not cache_file.exists():
        return {}

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Не удалось загрузить кэш {cache_file}: {e}")
        return {}


def _save_cache(cache_file: Path, cache_data: dict):
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = cache_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(cache_file)
    except Exception as e:
        logging.error(f"Не удалось сохранить кэш {cache_file}: {e}")


def _describe_image_task(image_path, page_num, img_index, vision_model, temperature):
    prompt = (
        "Ты анализируешь изображения из технических PDF-документов. "
        "Опиши изображение строго на русском языке. "
        "Если это схема, укажи блоки и связи между ними. "
        "Если это диаграмма, опиши, что она показывает. "
        "Если это фотография устройства, опиши объект и его роль в системе. "
        "Если это таблица или скан фрагмента документа, кратко перескажи содержимое. "
        "Ответ должен быть кратким, точным и полезным для написания технического текста."
    )

    logging.info(
        f"Старт анализа изображения: page={page_num + 1}, img={img_index}, model={vision_model}"
    )

    description = generate_from_image(
        prompt=prompt,
        image_path=str(image_path),
        model_name=vision_model,
        temperature=temperature
    )

    return {
        "page_num": page_num,
        "img_index": img_index,
        "image_path": str(image_path),
        "description": description
    }


def extract_data_from_pdf(
    file_path,
    output_image_dir="data/output/images",
    cache_file="data/output/image_cache/cache.json",
    vision_model="llava",
    temperature=0.1,
    analyze_images=True,
    max_images_per_page=1,
    min_image_width=500,
    min_image_height=300,
    max_workers=1,
    max_new_images_per_run=10
):
    file_path = Path(file_path).resolve()
    output_dir = Path(output_image_dir).resolve()
    cache_path = Path(cache_file).resolve()

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Не удалось создать директорию для изображений: {output_dir}. Ошибка: {e}")
        output_dir = None

    cache_data = _load_cache(cache_path)

    full_text_parts = []
    image_descriptions = []
    image_tasks = []

    cached_count = 0
    skipped_small_count = 0
    skipped_limit_count = 0

    try:
        document = fitz.open(str(file_path))
    except Exception as e:
        logging.error(f"Не удалось открыть PDF: {file_path}. Ошибка: {e}")
        return ""

    try:
        for page_num in range(len(document)):
            page = document.load_page(page_num)

            try:
                page_text = page.get_text()
                if page_text and page_text.strip():
                    full_text_parts.append(f"\n[СТРАНИЦА {page_num + 1}]\n{page_text}")
            except Exception as e:
                logging.warning(f"Не удалось извлечь текст со страницы {page_num + 1}: {e}")

            if not analyze_images or output_dir is None:
                continue

            try:
                image_list = page.get_images(full=True)
            except Exception as e:
                logging.warning(f"Не удалось получить изображения со страницы {page_num + 1}: {e}")
                continue

            selected_count = 0

            for img_index, img in enumerate(image_list):
                if selected_count >= max_images_per_page:
                    break

                try:
                    xref = img[0]
                    base_image = document.extract_image(xref)

                    image_bytes = base_image.get("image")
                    image_ext = base_image.get("ext", "png")
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)

                    if not image_bytes:
                        continue

                    if width < min_image_width or height < min_image_height:
                        skipped_small_count += 1
                        logging.info(
                            f"Пропуск маленького изображения: "
                            f"page={page_num + 1}, img={img_index}, size={width}x{height}"
                        )
                        continue

                    image_hash = _sha256_bytes(image_bytes)
                    cache_key = _make_cache_key(image_hash, vision_model)

                    if cache_key in cache_data:
                        cached_description = cache_data[cache_key].get("description", "")
                        if cached_description:
                            cached_count += 1
                            logging.info(
                                f"Описание изображения взято из кэша: "
                                f"page={page_num + 1}, img={img_index}, hash={image_hash[:12]}"
                            )
                            image_descriptions.append(
                                f"\n[ИЗОБРАЖЕНИЕ: страница {page_num + 1}, индекс {img_index}]\n"
                                f"{cached_description}"
                            )
                            selected_count += 1
                            continue

                    if len(image_tasks) >= max_new_images_per_run:
                        skipped_limit_count += 1
                        logging.info(
                            f"Пропуск нового изображения из-за лимита за запуск: "
                            f"page={page_num + 1}, img={img_index}"
                        )
                        continue

                    image_name = (
                        f"{file_path.stem}_page_{page_num + 1}_img_{img_index}_{image_hash[:12]}.{image_ext}"
                    )
                    image_path = output_dir / image_name

                    if not image_path.exists():
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        logging.info(f"Изображение сохранено: {image_path} ({width}x{height})")

                    image_tasks.append(
                        {
                            "image_path": image_path,
                            "page_num": page_num,
                            "img_index": img_index,
                            "image_hash": image_hash,
                            "cache_key": cache_key,
                            "width": width,
                            "height": height
                        }
                    )

                    selected_count += 1

                except Exception as e:
                    logging.warning(
                        f"Не удалось извлечь изображение: "
                        f"page={page_num + 1}, img={img_index}. Ошибка: {e}"
                    )

    finally:
        document.close()

    total_new = len(image_tasks)

    logging.info(
        f"PDF обработан: кэш={cached_count}, новых={total_new}, "
        f"пропущено маленьких={skipped_small_count}, "
        f"пропущено по лимиту={skipped_limit_count}"
    )

    if analyze_images and image_tasks:
        logging.info(
            f"Запуск анализа новых изображений. "
            f"Всего новых задач: {total_new}, workers={max_workers}"
        )

        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    _describe_image_task,
                    task["image_path"],
                    task["page_num"],
                    task["img_index"],
                    vision_model,
                    temperature
                ): task
                for task in image_tasks
            }

            for future in as_completed(future_map):
                task = future_map[future]
                completed += 1

                try:
                    result = future.result()
                    description = result["description"]

                    if description and not str(description).startswith("Ошибка"):
                        image_descriptions.append(
                            f"\n[ИЗОБРАЖЕНИЕ: страница {result['page_num'] + 1}, "
                            f"индекс {result['img_index']}]\n{description}"
                        )

                        with _cache_lock:
                            cache_data[task["cache_key"]] = {
                                "description": description,
                                "source_file": str(file_path),
                                "page": result["page_num"] + 1,
                                "image_index": result["img_index"],
                                "image_path": str(task["image_path"]),
                                "width": task["width"],
                                "height": task["height"],
                                "vision_model": vision_model,
                                "image_hash": task["image_hash"]
                            }
                            _save_cache(cache_path, cache_data)

                        logging.info(
                            f"[{completed}/{total_new}] Описание сохранено в кэш: "
                            f"page={result['page_num'] + 1}, "
                            f"img={result['img_index']}, "
                            f"hash={task['image_hash'][:12]}"
                        )
                    else:
                        logging.warning(
                            f"[{completed}/{total_new}] Не удалось получить описание изображения: "
                            f"{task['image_path']} -> {description}"
                        )

                except Exception as e:
                    logging.warning(f"[{completed}/{total_new}] Ошибка в задаче анализа изображения: {e}")

    result_parts = []

    if full_text_parts:
        result_parts.append("\n[ТЕКСТ ИЗ PDF]\n" + "\n".join(full_text_parts))

    if image_descriptions:
        result_parts.append("\n[ОПИСАНИЯ ИЗОБРАЖЕНИЙ]\n" + "\n".join(image_descriptions))

    return "\n".join(result_parts)
