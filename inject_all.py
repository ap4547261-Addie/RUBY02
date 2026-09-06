# inject_all.py
import os
import json
import sqlite3
import glob
from datetime import datetime
import time
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise Exception("GEMINI_API_KEY not set")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

DB_PATH = "ruby_memory.db"
DATA_FOLDER = "training_data"

def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if "messages" in data and isinstance(data["messages"], list):
        convo = ""
        for msg in data["messages"]:
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("content", "")
            if content:
                convo += f"{sender}: {content}\n"
        return convo

    if "conversations" in data and isinstance(data["conversations"], list):
        convo = ""
        for conv in data["conversations"]:
            messages = conv.get("messages", [])
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if content:
                    convo += f"{role}: {content}\n"
        return convo

    for key in ["messages", "conversation", "chat", "items"]:
        if key in data and isinstance(data[key], list):
            convo = ""
            for item in data[key]:
                sender = item.get("sender_name") or item.get("role") or item.get("from") or "Unknown"
                text = item.get("content") or item.get("text") or item.get("message") or ""
                if text:
                    convo += f"{sender}: {text}\n"
            if convo:
                return convo
    return ""

def generate_qa_pairs(conversation_text):
    prompt = f"""
You are Ruby. Extract key facts, opinions, and personality traits from this conversation.
Format each insight as a Q&A pair:
Q: [question]
A: [answer]

Skip anything personal (names, addresses, phone numbers). Keep it general.
Conversation:
{conversation_text}
"""
    response = model.generate_content(prompt)
    return response.text

def inject_qa_pairs(qa_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            category TEXT,
            importance INTEGER DEFAULT 3,
            timestamp INTEGER
        )
    ''')
    lines = qa_text.strip().split("\n")
    q = None
    for line in lines:
        if line.startswith("Q: "):
            q = line[3:].strip()
        elif line.startswith("A: ") and q:
            a = line[3:].strip()
            full = f"Q: {q}\nA: {a}"
            c.execute('''
                INSERT INTO memories (text, category, importance, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (full, "qa_pair", 3, int(datetime.now().timestamp())))
            q = None
    conn.commit()
    conn.close()

def process_all():
    json_files = glob.glob(f"{DATA_FOLDER}/**/*.json", recursive=True)
    if not json_files:
        print("No JSON files found in training_data/")
        return
    total = 0
    for path in json_files:
        convo = parse_file(path)
        if not convo or len(convo.split()) < 20:
            print(f"Skipping {path} – too short or unparseable.")
            continue
        print(f"Processing {path}...")
        qa = generate_qa_pairs(convo)
        inject_qa_pairs(qa)
        total += 1
        time.sleep(0.5)
    print(f"✅ Processed {total} files.")

if __name__ == "__main__":
    if not os.path.exists(DATA_FOLDER):
        print(f"Directory {DATA_FOLDER} not found. Skipping.")
    else:
        process_all()
