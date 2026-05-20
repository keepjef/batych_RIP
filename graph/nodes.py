import logging

from graph.state import GraphState
from llm.client import generate_text
from utils.docx_builder import save_section_to_docx
from utils.drawio_renderer import render_drawio_to_png


def init_project(state: GraphState):
    logging.info("Инициализация проекта. Ожидание ввода пользователя.")

    title = input("Введите название работы: ")
    problem = input("Введите проблему: ")
    goal = input("Введите цель работы: ")
    tasks = input("Введите задания на ВКР: ")

    return {
        "thesis_title": title,
        "problem_statement": problem,
        "thesis_goal": goal,
        "thesis_tasks": tasks
    }


def drafter(state: GraphState):
    current_iter = state.get("current_iteration", 0) + 1
    logging.info(
        f"Агент-Писатель начал работу (Итерация {current_iter} из {state.get('max_iterations')})."
    )

    with open("prompts/drafter_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = (
        f"{system_prompt}\n"
        f"Тема: {state.get('thesis_title', '')}\n"
        f"Проблема: {state.get('problem_statement', '')}\n"
        f"Цель: {state.get('thesis_goal', '')}\n"
        f"Задачи: {state.get('thesis_tasks', '')}\n"
        f"Раздел: {state.get('current_section', '')}\n"
        f"Правила: {state.get('pdf_context', '')}"
    )

    if state.get("user_decision"):
        prompt += f"\nУказание: {state['user_decision']}"

    model_name = state.get("llm_model", "qwen2.5:14b")
    temperature = state.get("temperature", 0.1)

    draft = generate_text(
        prompt,
        model_name=model_name,
        temperature=temperature
    )

    logging.info(f"Агент-Писатель успешно сгенерировал текст. Модель: {model_name}")
    return {
        "draft_text": draft,
        "user_decision": "",
        "current_iteration": current_iter
    }


def reviewer(state: GraphState):
    logging.info("Агент-Редактор проверяет черновик на соответствие правилам.")

    with open("prompts/reviewer_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = (
        f"{system_prompt}\n"
        f"Правила: {state.get('pdf_context', '')}\n"
        f"Черновик: {state.get('draft_text', '')}"
    )

    model_name = state.get("llm_model", "qwen2.5:14b")
    temperature = state.get("temperature", 0.1)

    review_result = generate_text(
        prompt,
        model_name=model_name,
        temperature=temperature
    )

    errors = []
    if "ОДОБРЕНО" not in review_result:
        logging.warning("Агент-Редактор нашел ошибки в тексте.")
        errors.append(review_result)
    else:
        logging.info("Текст ОДОБРЕНО Агентом-Редактором.")

    return {"errors": errors}


def error_gateway(state: GraphState):
    if state.get("human_mode"):
        logging.warning("Запуск шлюза. Требуется вмешательство человека.")
        print("Агент-Редактор нашел разночтения или предлагает варианты:")
        for error in state.get("errors", []):
            print(error)

        print("\n--- Текст черновика ---")
        print(state.get("draft_text", ""))
        print("-----------------------")

        decision = input("Введите правки для Писателя (или напишите 'ПРИНЯТЬ'): ")
        return {"user_decision": decision, "errors": []}

    logging.warning("Автономный режим. Формирование задания на исправление.")
    decision = "Исправь текст с учетом этих замечаний от редактора:\n" + "\n".join(
        state.get("errors", [])
    )
    return {"user_decision": decision, "errors": []}


def diagram_maker(state: GraphState):
    logging.info("Агент-Архитектор создает схему (XML для draw.io).")

    with open("prompts/diagram_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = f"{system_prompt}\nСделай схему для текста: {state.get('draft_text', '')}"

    model_name = state.get("llm_model", "qwen2.5:14b")
    temperature = state.get("temperature", 0.1)

    xml_code = generate_text(
        prompt,
        model_name=model_name,
        temperature=temperature
    )

    start = xml_code.find("<mxGraphModel>")
    end = xml_code.find("</mxGraphModel>")

    if start != -1 and end != -1:
        xml_code = xml_code[start:end + len("</mxGraphModel>")]

    logging.info(f"Схема успешно сгенерирована. Модель: {model_name}")
    return {"diagram_xml": xml_code}


def doc_writer(state: GraphState):
    logging.info("Сохранение результатов в Word-документ.")
    image_path = None

    if state.get("diagram_xml") and "<mxGraphModel>" in state.get("diagram_xml"):
        try:
            logging.info("Рендеринг XML в PNG изображение.")
            image_path = render_drawio_to_png(state["diagram_xml"])
        except Exception as e:
            logging.error(f"Ошибка рендеринга картинки: {e}")
            image_path = None

    save_section_to_docx(
        state.get("current_section", "Раздел"),
        state.get("draft_text", ""),
        image_path
    )

    logging.info("Раздел успешно сохранен в документ.")
    return {"diagram_xml": "", "draft_text": ""}
