# System-Brain-v1
Below is the full, detailed, from-zero README for System Brain v1 exactly as we built it on your Linux box, including the “real-world” issues we hit (Ollama service/port, CPU latency, strict JSON failures, circular import accident), and the precise commands + file contents so you can reproduce it without guessing.

⸻

System Brain v1

Offline Local Reasoning Engine (Linux-first)

What this is

System Brain v1 is a local CLI reasoning layer:
	•	Takes text input from stdin
	•	Calls a local LLM via Ollama on 127.0.0.1:11434
	•	Returns strict JSON to stdout
	•	Optionally logs results into a local SQLite DB

It is not a daemon, not an agent, and it does not auto-execute commands. It is meant to be stable, reproducible, and boring.

⸻

What this is not

System Brain v1 does not:
	•	Run background loops
	•	Execute shell commands automatically
	•	Modify system files automatically
	•	Install packages automatically
	•	Use cloud APIs after model pull
	•	Provide a web server, UI, or plugin framework

If you want those later, that’s a separate v2 scope. v1 stays frozen.

⸻

Requirements

Supported OS
	•	Ubuntu 22.04+ (tested on Ubuntu 24.04 “noble”)
	•	Debian-based distros should work

System requirements
	•	CPU-only is fine (slower)
	•	Disk space: model-dependent (Mistral pull ~4+ GB)
	•	Network required only for initial installs/model pull

⸻

Full install from a clean system (Ubuntu/Debian)

1) Update system packages

sudo apt update
sudo apt upgrade -y

2) Install required packages

This project is stdlib-only Python (no pip needed for v1):

sudo apt install -y python3 sqlite3 curl ca-certificates

Optional (not required):

sudo apt install -y jq htop


⸻

Install Ollama (local model runtime)

3) Install Ollama (official method)

curl -fsSL https://ollama.com/install.sh | sh

What this does on Ubuntu:
	•	Installs ollama to /usr/local/bin/ollama
	•	Creates a system user ollama
	•	Creates and enables ollama.service (systemd)
	•	Starts the service
	•	Listens on 127.0.0.1:11434

4) Verify Ollama installed

command -v ollama
ollama --version

5) Verify systemd service

systemctl status ollama --no-pager -l

6) Verify port listening

ss -ltnp | grep 11434 || true

Expected: a listener on 127.0.0.1:11434.

7) Pull a model

Recommended starter:

ollama pull mistral

Lighter model (faster on CPU):

ollama pull phi3

8) Confirm model is present

ollama list

9) Confirm inference works locally (baseline test)

echo "System integrity test." | ollama run mistral

You should see live output and return to prompt.

⸻

Project layout

Create this directory anywhere (we built it in ~/system-brain):

system-brain/
  brain.py
  config.py
  ollama_client.py
  schema.py
  memory.py
  README.md
  data/
    memory.sqlite   (created automatically if memory enabled)

Important: Python files do not need to be executable (chmod +x) because we run them via python3.

⸻

Create the project

1) Create folders + files

mkdir -p ~/system-brain/data
cd ~/system-brain
touch brain.py ollama_client.py schema.py memory.py config.py README.md


⸻

File contents (final v1)

config.py

import argparse
from pathlib import Path

DEFAULT_MODEL = "mistral"
DEFAULT_MODE = "advise"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_INPUT_CHARS = 200_000

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memory.sqlite"

def parse_args():
    parser = argparse.ArgumentParser(description="System Brain v1")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--mode", choices=["advise", "plan"], default=DEFAULT_MODE)
    parser.add_argument("--memory", action="store_true", help="Enable SQLite memory storage")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return parser.parse_args()

ollama_client.py (final)

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

schema.py (strict JSON contract + envelope fields)

import json
from datetime import datetime

REQUIRED_KEYS = [
    "summary",
    "observations",
    "recommendations",
    "confidence"
]

def validate_and_format(
    raw_text: str,
    mode: str,
    model: str,
    *,
    input_chars: int,
    truncated: bool
):
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError("Model did not return valid JSON.")

    for key in REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(data["confidence"], (int, float)):
        raise ValueError("Confidence must be numeric.")

    if not (0.0 <= float(data["confidence"]) <= 1.0):
        raise ValueError("Confidence must be between 0.0 and 1.0.")

    return {
        "mode": mode,
        "model": model,
        "input_chars": int(input_chars),
        "truncated": bool(truncated),
        "summary": data["summary"],
        "observations": data["observations"],
        "recommendations": data["recommendations"],
        "confidence": float(data["confidence"]),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

memory.py (optional SQLite logging)

import sqlite3
from pathlib import Path
from datetime import datetime

def init_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            input_text TEXT,
            summary TEXT,
            confidence REAL
        )
    """)
    conn.commit()
    return conn

def store(conn, input_text, summary, confidence):
    conn.execute(
        "INSERT INTO memory (timestamp, input_text, summary, confidence) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat() + "Z", input_text, summary, confidence)
    )
    conn.commit()

brain.py (final orchestrator)

import sys
import json
from config import parse_args, DB_PATH, DEFAULT_MAX_INPUT_CHARS
from ollama_client import generate
from schema import validate_and_format
import memory

def read_stdin():
    data = sys.stdin.read()
    original_length = len(data)
    truncated = original_length > DEFAULT_MAX_INPUT_CHARS

    if truncated:
        data = data[:DEFAULT_MAX_INPUT_CHARS]

    return data.strip(), original_length, truncated

def build_prompt(user_input: str, mode: str):
    base_instruction = (
        "You are a deterministic engineering reasoning engine.\n"
        "Respond ONLY in valid JSON with keys:\n"
        "summary (string), observations (list), recommendations (list), confidence (0.0-1.0).\n"
        "No extra text.\n"
    )

    if mode == "plan":
        base_instruction += "Provide actionable step-by-step recommendations.\n"

    return f"{base_instruction}\nInput:\n{user_input}"

def main():
    args = parse_args()

    user_input, input_chars, truncated = read_stdin()

    if not user_input:
        print(json.dumps({"error": "No input provided."}))
        sys.exit(1)

    prompt = build_prompt(user_input, args.mode)

    try:
        raw_output = generate(args.model, prompt, args.timeout)

        validated = validate_and_format(
            raw_output,
            args.mode,
            args.model,
            input_chars=input_chars,
            truncated=truncated
        )

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if args.memory:
        conn = memory.init_db(DB_PATH)
        memory.store(conn, user_input, validated["summary"], validated["confidence"])
        conn.close()

    print(json.dumps(validated, indent=2))

if __name__ == "__main__":
    main()


⸻

Running System Brain

Basic test

echo "Quick sanity test." | python3 ~/system-brain/brain.py --model mistral --timeout 120

Expected output (example):

{
  "mode": "advise",
  "model": "mistral",
  "input_chars": 19,
  "truncated": false,
  "summary": "...",
  "observations": [],
  "recommendations": [],
  "confidence": 1.0,
  "timestamp": "..."
}

Plan mode (advisory plan, still JSON)

echo "Give a step-by-step plan to debug DNS." | python3 ~/system-brain/brain.py --mode plan --model mistral --timeout 120

Journal input example

journalctl -n 200 | python3 ~/system-brain/brain.py --model mistral --timeout 120

Enable SQLite memory logging

echo "Memory test entry." | python3 ~/system-brain/brain.py --memory --model mistral --timeout 120

Inspect DB:

sqlite3 ~/system-brain/data/memory.sqlite \
  "select id,timestamp,confidence,summary from memory order by id desc limit 5;"


⸻

Validation / freeze checks

Compile check (catches syntax and import issues)

python3 -m py_compile ~/system-brain/*.py

Confirm Ollama endpoint health

curl -s http://127.0.0.1:11434/api/tags | head -80


⸻

Known issues and how to fix them

1) Connection refused when running brain.py

Symptom:

{"error":"Ollama connection failed: <urlopen error [Errno 111] Connection refused>"}

Cause: Ollama service not running, or not listening on port 11434.

Fix:

systemctl status ollama --no-pager -l
sudo systemctl start ollama
ss -ltnp | grep 11434 || true


⸻

2) bind: address already in use when running ollama serve

Cause: Ollama is already running under systemd (normal after install).

Fix: Do not run ollama serve manually. Use systemd:

sudo systemctl restart ollama


⸻

3) “It looks stuck / takes a while”

Cause: CPU-only inference + stream:false waits for full completion.

Fix options:
	•	Wait (first run loads model; slower)
	•	Increase timeout:

... --timeout 180


	•	Use smaller model:

ollama pull phi3
echo "..." | python3 brain.py --model phi3 --timeout 120



⸻

4) {"error": "Model did not return valid JSON."}

This is not a crash. This is strict schema enforcement working.

Cause: Model returned extra text / markdown / “example JSON” instead of raw JSON.

You confirmed this via:

curl -s http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model":"mistral","prompt":"Return ONLY valid JSON ...","stream":false}'

and it returned explanatory text and markdown in "response".

Fix options (v1 choices):
	•	Accept strict behavior and retry prompts more narrowly
	•	Switch to a model that follows JSON more reliably
	•	(v2) add a JSON “salvage” layer that extracts the first {...} block (optional; not part of v1 freeze)

⸻

5) Circular import / “partially initialized module”

Cause: A file accidentally imported itself or got overwritten (we hit this once while editing).

Fix:
	•	Ensure ollama_client.py contains only the client code and does not contain:

from ollama_client import generate


	•	Run:

python3 -m py_compile ~/system-brain/*.py



⸻

Operational notes

About “closing the process”

python3 brain.py is not persistent. Once it prints JSON and returns to prompt, it’s done.

The only persistent component is the Ollama service:

sudo systemctl stop ollama
sudo systemctl start ollama

Normally you keep it running.

⸻

Reproducible “from scratch” checklist (fast version)
	1.	OS update:

sudo apt update && sudo apt upgrade -y


	2.	Required packages:

sudo apt install -y python3 sqlite3 curl ca-certificates


	3.	Install Ollama:

curl -fsSL https://ollama.com/install.sh | sh


	4.	Pull model:

ollama pull mistral


	5.	Create project + paste files:

mkdir -p ~/system-brain/data
# paste the 5 python files from this README


	6.	Validate:

python3 -m py_compile ~/system-brain/*.py


	7.	Run:

echo "Quick sanity test." | python3 ~/system-brain/brain.py --model mistral --timeout 120



⸻

Status: v1 frozen

At this point, System Brain v1 is a complete, stable baseline.

If you want, I can also generate a “single paste installer script” that creates the directory and writes all files in one go (still minimal, still deterministic).
