import base64
import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_text(prompt, model_name="qwen2.5:14b", temperature=0.1):
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            OLLAMA_URL,
            data=json.dumps(data),
            headers=headers,
            timeout=600
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.RequestException as e:
        return f"Ошибка соединения с Ollama: {e}"


def generate_from_image(prompt, image_path, model_name="llava", temperature=0.1):
    try:
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "images": [img_base64],
            "options": {
                "temperature": temperature
            }
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            OLLAMA_URL,
            data=json.dumps(data),
            headers=headers,
            timeout=600
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.RequestException as e:
        return f"Ошибка распознавания картинки: {e}"
