# engine/vector_store.py
import os
import sqlite3
import json
from datetime import datetime

class HybridMemorySystem:
    def __init__(self, sqlite_path="ruby_memory.db", pinecone_api_key=None, index_host=None):
        self.sqlite_path = sqlite_path
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.index_host = index_host or os.getenv("PINECONE_INDEX_HOST")
        
        # Local-only mode - no API calls for memory
        self.use_pinecone = False  # Force local-only
        
        # Store keys for reference but don't use them for memory
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        self._init_sqlite()
        self._migrate_schema()
        
        print(f"HybridMemorySystem initialized in LOCAL-ONLY mode (0 API calls for memory)")

    def _init_sqlite(self):
        """Initialize SQLite database with enhanced schema"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Main memories table with importance and timestamps
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT UNIQUE,
                importance INTEGER DEFAULT 1,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                category TEXT DEFAULT 'general'
            )
        """)
        
        # Stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default stats
        cursor.execute("""
            INSERT OR IGNORE INTO stats (key, value) 
            VALUES ('interaction_count', 0)
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO stats (key, value) 
            VALUES ('total_memories', 0)
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO stats (key, value) 
            VALUES ('important_memories', 0)
        """)
        
        # Create index for faster search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_text 
            ON memories(text)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_importance 
            ON memories(importance DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_created 
            ON memories(created_at DESC)
        """)
        
        conn.commit()
        conn.close()

    def _migrate_schema(self):
        """Migrate old schema to new one if needed"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Check if old 'fact' column exists
            cursor.execute("PRAGMA table_info(memories)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'fact' in columns and 'text' not in columns:
                # Rename fact to text
                cursor.execute("ALTER TABLE memories RENAME COLUMN fact TO text")
                print("Migrated 'fact' column to 'text'")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Migration error: {e}")

    def increment_interaction(self) -> int:
        """Increment and return interaction count"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE stats 
            SET value = value + 1, updated_at = CURRENT_TIMESTAMP 
            WHERE key = 'interaction_count'
        """)
        cursor.execute("SELECT value FROM stats WHERE key = 'interaction_count'")
        count = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return count

    def get_interaction_count(self) -> int:
        """Get current interaction count"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM stats WHERE key = 'interaction_count'")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def save_hybrid_memory(self, fact: str, importance: int = 1, category: str = 'general'):
        """Save a memory to SQLite - 0 API calls"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO memories (text, importance, category, created_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (fact, importance, category))
            
            # Update total memories count
            cursor.execute("""
                UPDATE stats 
                SET value = value + 1, updated_at = CURRENT_TIMESTAMP 
                WHERE key = 'total_memories'
            """)
            
            if importance >= 3:
                cursor.execute("""
                    UPDATE stats 
                    SET value = value + 1, updated_at = CURRENT_TIMESTAMP 
                    WHERE key = 'important_memories'
                """)
            
            conn.commit()
            conn.close()
            print(f"Memory saved: {fact[:50]}... (importance: {importance})")
        except Exception as e:
            print(f"SQLite Save Error: {e}")

    def search_memories(self, query: str, limit: int = None) -> str:
        """Search local memories - 0 API calls, just SQLite - NO LIMIT"""
        memories_found = []
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Split query into keywords for better matching
            keywords = query.lower().split()
            
            # Build dynamic WHERE clause
            if keywords:
                conditions = []
                params = []
                for kw in keywords:
                    if len(kw) > 2:  # Skip very short words
                        conditions.append("LOWER(text) LIKE ?")
                        params.append(f"%{kw}%")
                
                if conditions:
                    sql = f"""
                        SELECT text, importance, created_at 
                        FROM memories 
                        WHERE {' OR '.join(conditions)}
                        ORDER BY importance DESC, created_at DESC
                    """
                    cursor.execute(sql, params)
                else:
                    # Fallback to most recent
                    cursor.execute("""
                        SELECT text, importance, created_at 
                        FROM memories 
                        ORDER BY importance DESC, created_at DESC
                    """)
            else:
                # No keywords - return most recent
                cursor.execute("""
                    SELECT text, importance, created_at 
                    FROM memories 
                    ORDER BY importance DESC, created_at DESC
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Format results with context
            for text, importance, created_at in rows:
                if text not in memories_found:
                    # Add importance indicator
                    if importance >= 3:
                        prefix = "🔴 Important: "
                    elif importance >= 2:
                        prefix = "🟡 "
                    else:
                        prefix = "🟢 "
                    memories_found.append(f"{prefix}{text}")
            
        except Exception as e:
            print(f"SQLite Read Error: {e}")
            return "No deep memories formed yet."

        if not memories_found:
            return "No deep memories formed yet."
        
        return ", ".join(memories_found)

    def get_memories_by_category(self, category: str, limit: int = None) -> list:
        """Get memories by category - NO LIMIT"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, importance, created_at 
                FROM memories 
                WHERE category = ?
                ORDER BY importance DESC, created_at DESC
            """, (category,))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"Category search error: {e}")
            return []

    def get_recent_memories(self, limit: int = None) -> list:
        """Get most recent memories - NO LIMIT"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, created_at 
                FROM memories 
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"Recent memories error: {e}")
            return []

    def get_important_memories(self, limit: int = None) -> list:
        """Get most important memories - NO LIMIT"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, created_at 
                FROM memories 
                WHERE importance >= 3
                ORDER BY importance DESC, created_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"Important memories error: {e}")
            return []

    def mark_memory_important(self, text: str):
        """Mark a memory as important"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories 
                SET importance = 3 
                WHERE text = ?
            """, (text,))
            conn.commit()
            conn.close()
            print(f"Memory marked as important: {text[:50]}...")
        except Exception as e:
            print(f"Mark important error: {e}")

    def cleanup_old_memories(self, days: int = 30):
        """Clean up old low-importance memories"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM memories 
                WHERE created_at < datetime('now', ?) 
                AND importance < 2
            """, (f'-{days} days',))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            print(f"Cleaned up {deleted} old memories")
        except Exception as e:
            print(f"Cleanup error: {e}")

    def get_stats(self) -> dict:
        """Get memory system stats"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            stats = {}
            cursor.execute("SELECT key, value FROM stats")
            for key, value in cursor.fetchall():
                stats[key] = value
            
            # Additional counts
            cursor.execute("SELECT COUNT(*) FROM memories")
            stats['total_memories'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memories WHERE importance >= 3")
            stats['important_memories'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memories WHERE category = 'general'")
            stats['general_memories'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            print(f"Stats error: {e}")
            return {}

    # ============================================
    # METHODS FOR RubyEngine COMPATIBILITY
    # ============================================

    def get_state(self) -> dict:
        """Get current state from stats table (for RubyEngine)"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM stats")
        rows = cursor.fetchall()
        conn.close()
        state = {}
        for key, value in rows:
            if key in ['interaction_count', 'total_memories', 'important_memories', 'conversations_today']:
                state[key] = int(value) if value else 0
            else:
                state[key] = value
        return state

    def update_state(self, new_state: dict):
        """Update state in stats table (for RubyEngine)"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        for key, value in new_state.items():
            cursor.execute("""
                INSERT INTO stats (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
            """, (key, str(value), str(value)))
        conn.commit()
        conn.close()

    def process(self, response: str, user_message: str):
        """Process response for memory extraction from [SAVE_MEMORY: ...] tags"""
        if "[SAVE_MEMORY:" in response:
            try:
                start = response.index("[SAVE_MEMORY:") + len("[SAVE_MEMORY:")
                end = response.index("]", start)
                fact = response[start:end].strip()
                if fact:
                    importance = 1
                    category = 'general'
                    
                    # Check for importance marker
                    if "IMPORTANT:" in fact:
                        parts = fact.split("IMPORTANT:")
                        fact = parts[0].strip()
                        importance = 3
                        category = 'important'
                    elif "CATEGORY:" in fact:
                        parts = fact.split("CATEGORY:")
                        fact = parts[0].strip()
                        category = parts[1].split()[0].strip() if len(parts) > 1 else 'general'
                    
                    self.save_hybrid_memory(fact, importance, category)
            except Exception as e:
                print(f"Memory extraction error: {e}")

    # ============================================

    def export_memories(self, filepath: str = "ruby_memories_export.json"):
        """Export all memories to JSON"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, importance, category, created_at 
                FROM memories 
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for text, importance, category, created_at in rows:
                memories.append({
                    "text": text,
                    "importance": importance,
                    "category": category,
                    "created_at": created_at
                })
            
            with open(filepath, 'w') as f:
                json.dump(memories, f, indent=2)
            
            print(f"Exported {len(memories)} memories to {filepath}")
            return filepath
        except Exception as e:
            print(f"Export error: {e}")
            return None

    def import_memories(self, filepath: str):
        """Import memories from JSON"""
        try:
            with open(filepath, 'r') as f:
                memories = json.load(f)
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            imported = 0
            for mem in memories:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO memories (text, importance, category, created_at) 
                        VALUES (?, ?, ?, ?)
                    """, (mem['text'], mem.get('importance', 1), mem.get('category', 'general'), mem.get('created_at', 'now')))
                    imported += 1
                except:
                    pass
            
            conn.commit()
            conn.close()
            print(f"Imported {imported} memories from {filepath}")
        except Exception as e:
            print(f"Import error: {e}")
