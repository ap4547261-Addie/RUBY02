#!/usr/bin/env python3
"""
inject_all.py – Final training data injector for Ruby's memory using local Ollama HTTP API 
with built-in project term blacklisting (Android compatible).
"""

import os
import json
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIG & BLACKLIST
# ============================================
STORAGE_DIR = os.path.expanduser("~/.ruby")
DB_PATH = os.path.join(STORAGE_DIR, "ruby_memory.db")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "tinyllama"

BLOCKED_KEYWORDS = [
    "ruby ai",
    "making ruby",
    "ruby app",
    "ruby prompt",
    "ruby architecture",
    "brainrouter",
    "energymanager",
    "rubysleepscheduler",
    "inject_all.py",
    "ruby_memory.db"
]

def should_block_content(text: str) -> bool:
    """Check if text contains any forbidden Ruby project or architecture keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in BLOCKED_KEYWORDS)

# ============================================
# OLLAMA Q&A GENERATOR (HTTP API - ANDROID SAFE)
# ============================================
def generate_qa_with_ollama(chunk: str) -> str:
    """Generate Q&A from a text chunk using local Ollama via HTTP."""
    if not chunk or len(chunk.strip()) < 20:
        return "Q: What is this?\nA: Not enough text to generate a meaningful Q&A."

    prompt = f"""Generate a question and answer from the following text. 
Output exactly in this format:
Q: <the question>
A: <the answer>

Text: {chunk}"""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            output = res_body.get("response", "").strip()

        if "Q:" in output and "A:" in output:
            lines = output.split("\n")
            q_lines = []
            a_lines = []
            mode = None
            for line in lines:
                if line.startswith("Q:"):
                    mode = "q"
                    q_lines.append(line[2:].strip())
                elif line.startswith("A:"):
                    mode = "a"
                    a_lines.append(line[2:].strip())
                elif mode == "q":
                    q_lines.append(line.strip())
                elif mode == "a":
                    a_lines.append(line.strip())
            if q_lines and a_lines:
                q = " ".join(q_lines)
                a = " ".join(a_lines)
                return f"Q: {q}\nA: {a}"
        
        return f"Q: What is the main idea?\nA: {chunk[:300]}..."
    except Exception as e:
        print(f"⚠️ Ollama HTTP error: {e}")
        return f"Q: What does this say?\nA: {chunk[:200]}..."

# ============================================
# DATABASE HELPERS
# ============================================
def init_db():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            importance INTEGER DEFAULT 3,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_at TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def count_existing():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM memories")
    count = c.fetchone()[0]
    conn.close()
    return count

def insert_memory(text, importance=3, category="qa_pair"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO memories (text, importance, category, created_at) VALUES (?, ?, ?, ?)",
        (text, importance, category, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ============================================
# PROCESS JSON FILES
# ============================================
def extract_text_from_json(data):
    """Recursively extract all string values from a JSON object."""
    if isinstance(data, str):
        return data
    elif isinstance(data, list):
        parts = []
        for item in data:
            parts.append(extract_text_from_json(item))
        return " ".join(parts)
    elif isinstance(data, dict):
        parts = []
        for key, value in data.items():
            if key in ["id", "timestamp", "created_at"]:
                continue
            parts.append(extract_text_from_json(value))
        return " ".join(parts)
    else:
        return ""

def parse_json_file(filepath):
    """Read JSON, extract text, split into chunks, filter blocked terms, generate Q&A."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ JSON parse error in {filepath}: {e}")
        return []

    text = extract_text_from_json(data)
    text = " ".join(text.split())
    if len(text) < 50:
        return []

    chunks = []
    current = []
    word_count = 0
    for sentence in text.replace("\n", ". ").split(". "):
        words = sentence.split()
        if word_count + len(words) > 300 and current:
            chunks.append(". ".join(current) + ".")
            current = []
            word_count = 0
        current.append(sentence)
        word_count += len(words)
    if current:
        chunks.append(". ".join(current) + ".")

    qa_pairs = []
    for chunk in chunks:
        if len(chunk) > 30:
            if should_block_content(chunk):
                print(f"🚫 Blocked project content chunk: {chunk[:40]}...")
                continue
                
            qa = generate_qa_with_ollama(chunk)
            if qa:
                if should_block_content(qa):
                    print(f"🚫 Blocked generated Q&A containing project terms.")
                    continue
                qa_pairs.append(qa)
    return qa_pairs

def main():
    print("🚀 RUBY TRAINING DATA INJECTOR (HTTP API + BLACKLIST)")
    init_db()

    json_files = []
    search_dirs = [".", "training_data"]
    for d in search_dirs:
        if os.path.exists(d):
            for file in os.listdir(d):
                if file.startswith("conversations-") and file.endswith(".json"):
                    full_path = os.path.join(d, file)
                    if full_path not in json_files:
                        json_files.append(full_path)

    if not json_files:
        print("⚠️ No conversation JSON files found in root or training_data directory.")
        return

    print(f"📊 Found {len(json_files)} JSON files to process")
    total_injected = 0

    for idx, filepath in enumerate(json_files, 1):
        print(f"\n[{idx}/{len(json_files)}] Processing: {filepath}")
        try:
            qa_pairs = parse_json_file(filepath)
            if not qa_pairs:
                print("⏭️  Skipping – no valid chunks")
                continue
            for qa in qa_pairs:
                insert_memory(qa, importance=3, category="qa_pair")
            total_injected += len(qa_pairs)
            print(f"✅ Injected {len(qa_pairs)} memory pairs")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    print("\n" + "="*50)
    print(f"✅ COMPLETE! Injected {total_injected} total memory pairs")
    print(f"📍 Database: {DB_PATH}")
    total = count_existing()
    print(f"📊 Memory Stats: Total: {total}")

if __name__ == "__main__":
    main()
            
