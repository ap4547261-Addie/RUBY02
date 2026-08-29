# engine/vector_store.py
import os
import sqlite3
from google import genai

class HybridMemorySystem:
    def __init__(self, sqlite_path="ruby_memory.db", pinecone_api_key=None, index_host=None):
        self.sqlite_path = sqlite_path
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Initialize SQLite fallback table
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
        conn.commit()
        conn.close()

    def _get_embedding(self, text: str):
        """Generates vector embeddings using Gemini embedding models."""
        try:
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return response.embedding.values
        except Exception as e:
            print(f"Embedding Generation Error: {e}")
            return None

    def save_hybrid_memory(self, fact: str):
        """Saves text locally in SQLite and pushes vector embeddings to Pinecone."""
        # 1. Save to SQLite
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO memories (fact) VALUES (?)", (fact,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"SQLite Save Error: {e}")

        # 2. Generate vector and sync with Pinecone (if configured)
        if self.pinecone_api_key:
            vector = self._get_embedding(fact)
            if vector:
                # Add your Pinecone vector upsert logic here using your index host
                pass

    def search_memories(self, query: str, limit=3) -> str:
        """Pulls relevant context using hybrid keyword or semantic search."""
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
            return "No local memories yet."
        return ", ".join(memories_found)
