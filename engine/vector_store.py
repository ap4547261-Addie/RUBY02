import os
import sqlite3
from google import genai

class HybridMemorySystem:
    def __init__(self, sqlite_path="ruby_memory.db", pinecone_api_key=None, index_host=None):
        self.sqlite_path = sqlite_path
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        
        # Fallback to an empty string or local config if environment variable is missing on mobile
        api_key = os.getenv("GEMINI_API_KEY") or "YOUR_FALLBACK_API_KEY_HERE"
        self.client = genai.Client(api_key=api_key)
        
        self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('interaction_count', 0)")
        conn.commit()
        conn.close()

    def increment_interaction(self) -> int:
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE stats SET value = value + 1 WHERE key = 'interaction_count'")
        cursor.execute("SELECT value FROM stats WHERE key = 'interaction_count'")
        count = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return count

    def get_interaction_count(self) -> int:
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM stats WHERE key = 'interaction_count'")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def save_hybrid_memory(self, fact: str):
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO memories (fact) VALUES (?)", (fact,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"SQLite Save Error: {e}")

    def search_memories(self, query: str, limit=5) -> str:
        memories_found = []
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT fact FROM memories ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                if row[0] not in memories_found:
                    memories_found.append(row[0])
        except Exception as e:
            print(f"SQLite Read Error: {e}")

        if not memories_found:
            return "No deep memories formed yet."
        return ", ".join(memories_found)
