import yaml
import os
import logging
import shutil
from graph.workflow import app
from utils.pdf_parser import extract_data_from_pdf
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(module)s: %(message)s")
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
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
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
                pdf_context_text += "\n[НОРМАТИВЫ]:\n" + extract_data_from_pdf(file_path)
    if os.path.exists(examples_dir):
        for filename in os.listdir(examples_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(examples_dir, filename)
                logging.info(f"Чтение примеров: {filename}")
                pdf_context_text += "\n[ПРИМЕРЫ ПРОШЛЫХ ЛЕТ]:\n" + extract_data_from_pdf(file_path)
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
        "current_iteration": 0
    }
    logging.info("Запуск графа генерации ВКР...")
    for output in app.stream(initial_state, config={"configurable": {"thread_id": "1"}}):
        for key, value in output.items():
            logging.info(f"--- Завершен узел: {key} ---")
if __name__ == "__main__":
    main()