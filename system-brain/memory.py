# memory.py
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
