import logging
import os
import shutil
import yaml

from graph.workflow import app
from utils.pdf_parser import extract_data_from_pdf


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(module)s: %(message)s"
)


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    pdf_context_text = ""

    control_dir = config.get("input_control", "data/input/control")
    examples_dir = config.get("input_examples", "data/input/examples")
    main_dir = config.get("input_main", "data/input/main")
    output_dir = config.get("output_path", "data/output")

    human_mode = config.get("human_mode", False)
    max_iterations = config.get("max_iterations", 3)

    llm_model = config.get("llm_model", "qwen2.5:14b")
    vision_model = config.get("vision_model", "llava")
    temperature = config.get("temperature", 0.1)

    analyze_images = config.get("analyze_images", True)
    max_images_per_page = config.get("max_images_per_page", 2)
    min_image_width = config.get("min_image_width", 300)
    min_image_height = config.get("min_image_height", 200)
    vision_workers = config.get("vision_workers", 2)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    images_dir = os.path.join(output_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    image_cache_dir = os.path.join(output_dir, "image_cache")
    if not os.path.exists(image_cache_dir):
        os.makedirs(image_cache_dir)

    image_cache_file = os.path.join(image_cache_dir, "cache.json")

    base_docx = os.path.join(output_dir, "thesis.docx")
    if not os.path.exists(base_docx) and os.path.exists(main_dir):
        for filename in os.listdir(main_dir):
            if filename.endswith(".docx"):
                shutil.copy(os.path.join(main_dir, filename), base_docx)
                logging.info(f"Взят базовый шаблон документа: {filename}")
                break

    if os.path.exists(control_dir):
        for filename in os.listdir(control_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(control_dir, filename)
                logging.info(f"Чтение нормативов: {filename}")
                pdf_context_text += "\n[НОРМАТИВЫ]:\n" + extract_data_from_pdf(
                    file_path=file_path,
                    output_image_dir=images_dir,
                    cache_file=image_cache_file,
                    vision_model=vision_model,
                    temperature=temperature,
                    analyze_images=analyze_images,
                    max_images_per_page=max_images_per_page,
                    min_image_width=min_image_width,
                    min_image_height=min_image_height,
                    max_workers=vision_workers
                )

    if os.path.exists(examples_dir):
        for filename in os.listdir(examples_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(examples_dir, filename)
                logging.info(f"Чтение примеров: {filename}")
                pdf_context_text += "\n[ПРИМЕРЫ ПРОШЛЫХ ЛЕТ]:\n" + extract_data_from_pdf(
                    file_path=file_path,
                    output_image_dir=images_dir,
                    cache_file=image_cache_file,
                    vision_model=vision_model,
                    temperature=temperature,
                    analyze_images=analyze_images,
                    max_images_per_page=max_images_per_page,
                    min_image_width=min_image_width,
                    min_image_height=min_image_height,
                    max_workers=vision_workers
                )

    initial_state = {
        "thesis_title": "",
        "problem_statement": "",
        "thesis_goal": "",
        "thesis_tasks": "",
        "current_section": "Введение",
        "draft_text": "",
        "pdf_context": pdf_context_text,
        "errors": [],
        "user_decision": "",
        "diagram_xml": "",
        "human_mode": human_mode,
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "llm_model": llm_model,
        "vision_model": vision_model,
        "temperature": temperature
    }

    logging.info(
        f"Запуск графа генерации ВКР... "
        f"LLM={llm_model}, vision={vision_model}, analyze_images={analyze_images}"
    )

    for output in app.stream(initial_state, config={"configurable": {"thread_id": "1"}}):
        for key, value in output.items():
            logging.info(f"--- Завершен узел: {key} ---")


if __name__ == "__main__":
    main()
