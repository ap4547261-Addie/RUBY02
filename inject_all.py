# inject_all.py – Universal training data injector (FIXED for ChatGPT mapping)
import os
import json
import sqlite3
import glob
from datetime import datetime
import time
import sys

# ============================================
# 1. DATABASE PATH – ROBUST SETUP
# ============================================
possible_paths = [
    os.getenv("FLET_APP_STORAGE_DATA"),
    os.path.expanduser("~/.ruby"),
    "./ruby_storage",
    "."
]

STORAGE_DIR = None
for path in possible_paths:
    if path:
        try:
            os.makedirs(path, exist_ok=True)
            STORAGE_DIR = path
            print(f"✅ Storage directory: {STORAGE_DIR}")
            break
        except Exception as e:
            print(f"⚠️ Could not use {path}: {e}")

if not STORAGE_DIR:
    STORAGE_DIR = "."
    print(f"⚠️ Defaulting to current directory: {STORAGE_DIR}")

DB_PATH = os.path.join(STORAGE_DIR, "ruby_memory.db")
DATA_FOLDER = "training_data"

print(f"📁 Database path: {DB_PATH}")
print(f"📂 Training data folder: {DATA_FOLDER}")

# ============================================
# 2. GEMINI SETUP (OPTIONAL)
# ============================================
API_KEY = os.getenv("GEMINI_API_KEY")
genai = None
model = None

if API_KEY:
    try:
        import google.generativeai as genai_lib
        genai_lib.configure(api_key=API_KEY)
        genai = genai_lib
        model = genai_lib.GenerativeModel("gemini-2.0-flash-exp")
        print("✅ Gemini API configured")
    except ImportError:
        print("⚠️ google-generativeai not installed. Will use fallback Q&A generation.")
    except Exception as e:
        print(f"⚠️ Gemini setup failed: {e}. Will use fallback.")
else:
    print("⚠️ GEMINI_API_KEY not set. Will use fallback Q&A generation.")

# ============================================
# 3. BLOCK LIST
# ============================================
BLOCKED_PHRASES = [
    "my name is", "my email", "my phone", "my address", "my birthday",
    "I am creating Ruby", "I am building Ruby", "building an AI", "creating an AI",
    "Ruby is an AI", "Ruby's code", "programming Ruby", "developer of Ruby",
    "I am a developer", "I am working on Ruby", "Ruby's personality", "training Ruby",
    "local brain", "gemini key", "api key",
]

def is_blocked(text):
    text_lower = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in text_lower:
            return True
    return False

# ============================================
# 4. FILE PARSING (SUPPORTS ALL FORMATS)
# ============================================
def parse_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse {file_path}: {e}")
        return ""

    # ---- ChatGPT export with 'mapping' (new format) ----
    if isinstance(data, list) and len(data) > 0 and "mapping" in data[0]:
        convo = ""
        for conv in data:
            mapping = conv.get("mapping", {})
            for node_id, node in mapping.items():
                message = node.get("message")
                if message:
                    author_role = message.get("author", {}).get("role", "unknown")
                    content_parts = message.get("content", {}).get("parts", [])
                    if content_parts:
                        # Extract text from parts (which may be dicts with 'text' field)
                        texts = []
                        for part in content_parts:
                            if isinstance(part, dict):
                                texts.append(part.get("text", ""))
                            else:
                                texts.append(str(part))
                        content_text = " ".join(texts)
                        convo += f"{author_role}: {content_text}\n"
        if convo:
            return convo

    # ---- Instagram format ----
    if "messages" in data and isinstance(data["messages"], list):
        convo = ""
        for msg in data["messages"]:
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("content", "")
            if content:
                convo += f"{sender}: {content}\n"
        if convo:
            return convo

    # ---- ChatGPT format (old, with "conversations" key) ----
    if "conversations" in data and isinstance(data["conversations"], list):
        convo = ""
        for conv in data["conversations"]:
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if content:
                    convo += f"{role}: {content}\n"
        if convo:
            return convo

    # ---- Generic fallback ----
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
# 5. Q&A GENERATION (Gemini or fallback)
# ============================================
def generate_qa_pairs(conversation_text):
    if genai and model:
        try:
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
        except Exception as e:
            print(f"⚠️ Gemini API error: {e}. Using fallback.")

    print("🔄 Using fallback Q&A generation (no Gemini)")
    sentences = [s.strip() for s in conversation_text.split('.') if s.strip()]
    qa_pairs = []
    for i, sentence in enumerate(sentences[:10]):
        if len(sentence.split()) > 5:
            qa_pairs.append(f"Q: What did you learn from: {sentence}?")
            qa_pairs.append(f"A: {sentence}")
    return "\n".join(qa_pairs)

# ============================================
# 6. DATABASE OPERATIONS
# ============================================
def init_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
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
        c.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('interaction_count', '0')")
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {DB_PATH}")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def inject_qa_pairs(qa_text):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        lines = qa_text.strip().split("\n")
        q = None
        injected = 0
        for line in lines:
            if line.startswith("Q: "):
                q = line[3:].strip()
            elif line.startswith("A: ") and q:
                a = line[3:].strip()
                full = f"Q: {q}\nA: {a}"
                if is_blocked(full):
                    q = None
                    continue
                c.execute('SELECT id FROM memories WHERE text=?', (full,))
                if not c.fetchone():
                    c.execute('''
                        INSERT INTO memories (text, category, importance, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (full, "qa_pair", 3, datetime.now().isoformat()))
                    injected += 1
                q = None
        conn.commit()
        conn.close()
        return injected
    except Exception as e:
        print(f"❌ Injection failed: {e}")
        return 0

# ============================================
# 7. MAIN PROCESSING
# ============================================
def process_all():
    if not init_database():
        return False
    if not os.path.exists(DATA_FOLDER):
        print(f"⚠️ Directory '{DATA_FOLDER}' not found. Creating example...")
        os.makedirs(DATA_FOLDER, exist_ok=True)
        example = {
            "messages": [
                {"sender_name": "User", "content": "What do you think about technology?"},
                {"sender_name": "Ruby", "content": "I find technology fascinating but also complicated."},
                {"sender_name": "User", "content": "Do you have any hobbies?"},
                {"sender_name": "Ruby", "content": "I enjoy learning new things and having deep conversations."}
            ]
        }
        with open(os.path.join(DATA_FOLDER, "example.json"), 'w') as f:
            json.dump(example, f, indent=2)
        print(f"✅ Created example file: {DATA_FOLDER}/example.json")
        print(f"📝 Add your conversation JSON files to '{DATA_FOLDER}/'")
        return True

    json_files = glob.glob(f"{DATA_FOLDER}/**/*.json", recursive=True)
    if not json_files:
        print(f"❌ No JSON files found in '{DATA_FOLDER}/'")
        return False

    print(f"📊 Found {len(json_files)} JSON files to process")
    total_injected = 0
    for i, path in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] Processing: {path}")
        convo = parse_file(path)
        if not convo or len(convo.split()) < 20:
            print(f"⏭️  Skipping – too short or unparseable")
            continue
        print(f"✅ Parsed {len(convo.split())} words")
        qa = generate_qa_pairs(convo)
        injected = inject_qa_pairs(qa)
        print(f"✅ Injected {injected} memory pairs")
        total_injected += injected
        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"✅ COMPLETE! Injected {total_injected} total memory pairs")
    print(f"📍 Database: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM memories")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM memories WHERE importance >= 3")
        important = c.fetchone()[0]
        conn.close()
        print(f"📊 Memory Stats: Total: {total}, Important: {important}")
    except:
        pass
    return True

if __name__ == "__main__":
    print("🚀 RUBY TRAINING DATA INJECTOR\n")
    success = process_all()
    sys.exit(0 if success else 1)
