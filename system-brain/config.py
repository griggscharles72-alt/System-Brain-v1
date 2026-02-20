# config.py
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
