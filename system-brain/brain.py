# brain.py
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
