# ollama_client.py
import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def generate(model: str, prompt: str, timeout: int):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "top_p": 1,
            "repeat_penalty": 1.1,
            "num_predict": 400
        }
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)

            if "response" not in data:
                raise RuntimeError("Ollama response missing 'response' field.")

            return data["response"]

    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama connection failed: {e}")

    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON returned from Ollama.")
