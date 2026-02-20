# schema.py
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
