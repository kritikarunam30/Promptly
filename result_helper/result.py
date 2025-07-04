import requests

def get_result(user_prompt):
    API_KEY = "# Enter API KEY"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3.3-8b-instruct:free",  # Free model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result ["choices"][0]["message"]["content"]
    else:
        print("Status Code:", response.status_code)
        return response.text