import requests
import json
import base64
def generate_text(prompt, model_name="qwen2.5:14b"):
    url = "http://10.160.165.12:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result["response"]
    return "Ошибка соединения"
def generate_from_image(prompt, image_path, model_name="llava"):
    with open(image_path, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode("utf-8")
    url = "http://10.160.165.12:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "images": [img_base64]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result["response"]
    return "Ошибка распознавания картинки"