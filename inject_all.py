# inject_all.py – Universal training data injector (fixed for app compatibility)
import os
import json
import sqlite3
import glob
from datetime import datetime
import time
import google.generativeai as genai

# ============================================
# 1. DATABASE PATH – same as the running app
# ============================================
STORAGE_DIR = os.getenv("FLET_APP_STORAGE_DATA", ".")
os.makedirs(STORAGE_DIR, exist_ok=True)
DB_PATH = os.path.join(STORAGE_DIR, "ruby_memory.db")
DATA_FOLDER = "training_data"

# ============================================
# 2. GEMINI SETUP
# ============================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise Exception("GEMINI_API_KEY not set")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ============================================
# 3. BLOCK LIST – skip personal and creation‑related content
# ============================================
BLOCKED_PHRASES = [
    # Personal info
    "my name is",
    "my email",
    "my phone",
    "my address",
    "my birthday",
    # Ruby's creation / development
    "I am creating Ruby",
    "I am building Ruby",
    "building an AI",
    "creating an AI",
    "Ruby is an AI",
    "Ruby's code",
    "programming Ruby",
    "developer of Ruby",
    "I am a developer",
    "I am working on Ruby",
    "Ruby's personality",
    "training Ruby",
    "local brain",
    "gemini key",
    "api key",
    # Add any other names/phrases you want to block
    # "YourName",
]

def is_blocked(text):
    """Return True if text contains any blocked phrase (case‑insensitive)."""
    text_lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in text_lower:
            return True
    return False

# ============================================
# 4. FILE PARSING (supports Instagram, ChatGPT, etc.)
# ============================================
def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Instagram format
    if "messages" in data and isinstance(data["messages"], list):
        convo = ""
        for msg in data["messages"]:
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("content", "")
            if content:
                convo += f"{sender}: {content}\n"
        return convo

    # ChatGPT format
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

    # Generic fallback
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

# ============================================
# 5. GEMINI Q&A GENERATION
# ============================================
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

# ============================================
# 6. INJECT INTO DATABASE (app‑compatible schema)
# ============================================
def inject_qa_pairs(qa_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create tables matching HybridMemorySystem
    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT UNIQUE,
            importance INTEGER DEFAULT 1,
            synced INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            category TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        INSERT OR IGNORE INTO stats (key, value) VALUES ('interaction_count', '0')
    ''')

    lines = qa_text.strip().split("\n")
    q = None
    for line in lines:
        if line.startswith("Q: "):
            q = line[3:].strip()
        elif line.startswith("A: ") and q:
            a = line[3:].strip()
            full = f"Q: {q}\nA: {a}"
            # Skip if blocked
            if is_blocked(full):
                q = None
                continue
            # Avoid duplicates
            c.execute('SELECT id FROM memories WHERE text=?', (full,))
            if not c.fetchone():
                c.execute('''
                    INSERT INTO memories (text, category, importance, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (full, "qa_pair", 3, datetime.now().isoformat()))
            q = None
    conn.commit()
    conn.close()

# ============================================
# 7. PROCESS ALL FILES IN training_data/
# ============================================
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
        time.sleep(0.5)   # avoid rate limits
    print(f"✅ Processed {total} files.")

# ============================================
# 8. MAIN
# ============================================
if __name__ == "__main__":
    if not os.path.exists(DATA_FOLDER):
        print(f"Directory {DATA_FOLDER} not found. Skipping.")
    else:
        process_all()
