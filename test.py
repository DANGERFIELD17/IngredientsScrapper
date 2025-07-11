import requests

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:latest",  # Use your actual model name as shown in 'ollama list'
            "prompt": "what is your word limit?",
            "stream": False
        },
        timeout=60
    )

    if response.ok:
        print(response.json().get('response', response.text))
    else:
        print(f"Error: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

