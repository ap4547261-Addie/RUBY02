#!/usr/bin/env python3
"""
inject_all.py – Injects training data into Ruby's memory using local Ollama LLM.
"""

import os
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIG
# ============================================
STORAGE_DIR = os.path.expanduser("~/.ruby")
DB_PATH = os.path.join(STORAGE_DIR, "ruby_memory.db")
TRAINING_DIR = "training_data"          # folder with JSON files

# Ollama model – adjust if you use a different one
OLLAMA_MODEL = "phi3:3.8b-mini-4k-instruct-q4_K_M"  # or "tinyllama"

# ============================================
# OLLAMA Q&A GENERATOR
# ============================================
def generate_qa_with_ollama(chunk: str) -> str:
    """Generate Q&A from a text chunk using local Ollama."""
    if not chunk or len(chunk.strip()) < 20:
        return "Q: What is this?\nA: Not enough text to generate a meaningful Q&A."

    prompt = f"""Generate a question and answer from the following text. 
Output exactly in this format:
Q: <the question>
A: <the answer>

Text: {chunk}"""

    try:
        cmd = ["ollama", "run", OLLAMA_MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        output = result.stdout.strip()
        if "Q:" in output and "A:" in output:
            # Ensure it's properly formatted
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
            else:
                return f"Q: What is the main idea?\nA: {chunk[:300]}..."
        else:
            # fallback
            return f"Q: What is the key point?\nA: {chunk[:300]}..."
    except subprocess.TimeoutExpired:
        return f"Q: What is this about?\nA: {chunk[:200]}..."
    except Exception as e:
        print(f"⚠️ Ollama error: {e}")
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
    """Read JSON, extract text, split into chunks, generate Q&A."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ JSON parse error: {e}")
        return []

    text = extract_text_from_json(data)
    # Clean up whitespace
    text = " ".join(text.split())
    if len(text) < 50:
        return []

    # Split into paragraphs / sentences
    # Simple: split by newline or period, but keep chunks of ~300 words
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

    # Generate Q&A for each chunk
    qa_pairs = []
    for chunk in chunks:
        if len(chunk) > 30:
            qa = generate_qa_with_ollama(chunk)
            if qa:
                qa_pairs.append(qa)
    return qa_pairs

def main():
    print("🚀 RUBY TRAINING DATA INJECTOR (Ollama)")
    init_db()

    if not os.path.exists(TRAINING_DIR):
        print(f"⚠️ Training directory '{TRAINING_DIR}' not found.")
        return

    json_files = []
    for root, _, files in os.walk(TRAINING_DIR):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

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
