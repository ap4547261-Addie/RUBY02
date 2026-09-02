# tools/data_ingestion.py
import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict


class DataIngestion:
    """
    Local-Only Data Ingestion for Ruby's Brain
    0 API calls - Everything runs locally
    """
    
    def __init__(self, db_path="ruby_knowledge.db"):
        self.db_path = db_path
        self._init_db()
        print("📚 DataIngestion initialized in LOCAL-ONLY mode (0 API calls)")
    
    def _init_db(self):
        """Initialize SQLite database for local knowledge"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Knowledge chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                text TEXT,
                source_file TEXT,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        # Keywords table for fast searching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                chunk_id TEXT,
                FOREIGN KEY (chunk_id) REFERENCES knowledge_chunks (chunk_id)
            )
        """)
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize default categories
        default_categories = [
            ("general", "General knowledge"),
            ("instagram", "Instagram learning"),
            ("fashion", "Fashion and style"),
            ("psychology", "Psychology insights"),
            ("personal", "Personal experiences"),
            ("tech", "Technology and coding")
        ]
        
        for name, description in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, description) 
                VALUES (?, ?)
            """, (name, description))
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_text ON knowledge_chunks(text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON keywords(keyword)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_category ON knowledge_chunks(category)")
        
        conn.commit()
        conn.close()
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks - 0 API calls"""
        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings locally - 0 API calls"""
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            # Simple hash-based vector
            words = text.lower().split()[:100]
            vector = []
            for word in words:
                hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16) % 1000
                vector.append(hash_val / 1000.0)
            
            while len(vector) < 384:
                vector.append(0.0)
            
            embeddings.append(vector[:384])
        
        return embeddings
    
    def process_document(self, file_path: str, category: str = "general") -> List[Dict]:
        """Process a local document - 0 API calls"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
        
        chunks = self.chunk_text(content)
        processed_data = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{os.path.basename(file_path)}_chunk_{i}"
            
            cursor.execute("SELECT id FROM knowledge_chunks WHERE chunk_id = ?", (chunk_id,))
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO knowledge_chunks (chunk_id, text, source_file, category)
                    VALUES (?, ?, ?, ?)
                """, (chunk_id, chunk, file_path, category))
                
                words = set(chunk.lower().split())
                for word in list(words)[:20]:
                    if len(word) > 3:
                        cursor.execute("""
                            INSERT INTO keywords (keyword, chunk_id)
                            VALUES (?, ?)
                        """, (word, chunk_id))
                
                processed_data.append({
                    "id": chunk_id,
                    "text": chunk,
                    "source": file_path,
                    "category": category
                })
        
        conn.commit()
        conn.close()
        
        print(f"📚 Processed {len(chunks)} chunks from {file_path}")
        return processed_data
    
    def search_knowledge(self, query: str, limit: int = None) -> List[Dict]:
        """Search local knowledge - 0 API calls - NO LIMIT"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords = query.lower().split()
        keyword_conditions = []
        params = []
        
        for kw in keywords:
            if len(kw) > 2:
                keyword_conditions.append("keyword = ?")
                params.append(kw)
        
        if keyword_conditions:
            sql = f"""
                SELECT DISTINCT k.chunk_id, k.text, k.category, k.importance, k.access_count
                FROM knowledge_chunks k
                JOIN keywords kw ON k.chunk_id = kw.chunk_id
                WHERE {' OR '.join(keyword_conditions)}
                ORDER BY k.importance DESC, k.access_count DESC
            """
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT chunk_id, text, category, importance, access_count
                FROM knowledge_chunks
                WHERE text LIKE ?
                ORDER BY importance DESC, access_count DESC
            """, (f"%{query}%",))
            rows = cursor.fetchall()
        
        results = []
        for chunk_id, text, category, importance, access_count in rows:
            cursor.execute("""
                UPDATE knowledge_chunks 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE chunk_id = ?
            """, (chunk_id,))
            
            results.append({
                "id": chunk_id,
                "text": text,
                "category": category,
                "importance": importance,
                "access_count": access_count
            })
        
        conn.commit()
        conn.close()
        
        return results
    
    def learn_from_text(self, text: str, category: str = "general", importance: int = 1) -> Dict:
        """Learn from new text - 0 API calls"""
        chunks = self.chunk_text(text, chunk_size=500, overlap=100)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"learned_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            
            cursor.execute("""
                INSERT INTO knowledge_chunks (chunk_id, text, category, importance, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (chunk_id, chunk, category, importance))
            
            words = set(chunk.lower().split())
            for word in list(words)[:15]:
                if len(word) > 3:
                    cursor.execute("""
                        INSERT INTO keywords (keyword, chunk_id)
                        VALUES (?, ?)
                    """, (word, chunk_id))
            
            processed.append({
                "id": chunk_id,
                "text": chunk,
                "category": category
            })
        
        conn.commit()
        conn.close()
        
        print(f"📚 Learned {len(chunks)} chunks from text")
        return {"chunks": processed, "count": len(chunks)}
    
    def learn_from_instagram(self, comment: str, username: str) -> Dict:
        """Learn from Instagram comments - 0 API calls"""
        learning_text = f"Instagram user {username} said: {comment}"
        return self.learn_from_text(learning_text, category="instagram", importance=2)
    
    def learn_from_document(self, file_path: str, category: str = "general") -> Dict:
        """Learn from a document - 0 API calls"""
        result = self.process_document(file_path, category)
        return {
            "chunks": result,
            "count": len(result),
            "source": file_path
        }
    
    def get_knowledge_summary(self) -> Dict:
        """Get summary of knowledge - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_chunks")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT category, COUNT(*) FROM knowledge_chunks 
            GROUP BY category
        """)
        categories = cursor.fetchall()
        
        cursor.execute("""
            SELECT chunk_id, text, access_count, category
            FROM knowledge_chunks
            ORDER BY access_count DESC
        """)
        most_accessed = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_chunks": total_chunks,
            "categories": dict(categories),
            "most_accessed": [
                {"id": row[0], "text": row[1][:50] + "...", "access_count": row[2], "category": row[3]}
                for row in most_accessed
            ]
        }
    
    def export_knowledge(self, file_path: str = "ruby_knowledge_export.json") -> str:
        """Export all knowledge - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chunk_id, text, source_file, category, importance, created_at, access_count
            FROM knowledge_chunks
            ORDER BY importance DESC, created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_chunks": len(rows),
            "chunks": [
                {
                    "id": row[0],
                    "text": row[1],
                    "source": row[2],
                    "category": row[3],
                    "importance": row[4],
                    "created_at": row[5],
                    "access_count": row[6]
                }
                for row in rows
            ]
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📚 Exported {len(rows)} chunks to {file_path}")
        return file_path
    
    def import_knowledge(self, file_path: str) -> Dict:
        """Import knowledge from export - 0 API calls"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "File not found"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        imported = 0
        for chunk in data.get("chunks", []):
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO knowledge_chunks 
                    (chunk_id, text, source_file, category, importance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk["id"],
                    chunk["text"],
                    chunk.get("source", "imported"),
                    chunk.get("category", "general"),
                    chunk.get("importance", 1),
                    chunk.get("created_at", datetime.now().isoformat())
                ))
                imported += 1
            except Exception as e:
                print(f"Import error: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"📚 Imported {imported} chunks from {file_path}")
        return {
            "success": True,
            "imported": imported,
            "total": len(data.get("chunks", []))
        }
