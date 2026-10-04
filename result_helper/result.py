import os
import requests

def get_result(user_prompt):
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result ["choices"][0]["message"]["content"]
    else:
        print("Status Code:", response.status_code)
        return response.text