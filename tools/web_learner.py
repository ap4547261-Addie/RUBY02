# tools/web_learner.py
import urllib.request
import urllib.parse
import json
import re
import sqlite3
from datetime import datetime
from typing import Dict, List
from tools.data_ingestion import DataIngestion


class WebLearner:
    """Ruby's Web Learning System - Learns from web pages - 0 API calls"""
    
    def __init__(self, data_ingestion: DataIngestion, db_path="ruby_web_knowledge.db"):
        self.data_ingestion = data_ingestion
        self.db_path = db_path
        self._init_db()
        print("🌐 WebLearner initialized - Ruby can learn from the web!")
    
    def _init_db(self):
        """Initialize web knowledge database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                category TEXT DEFAULT 'web'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                content TEXT,
                content_hash TEXT UNIQUE,
                importance INTEGER DEFAULT 1,
                learned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_url) REFERENCES web_sources (url)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                content_id INTEGER,
                FOREIGN KEY (content_id) REFERENCES web_content (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def fetch_url(self, url: str) -> str:
        """Fetch content from a URL - 0 API calls"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RubyEngine/1.0"}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_bytes = response.read()
                html_text = html_bytes.decode('utf-8', errors='ignore')
                
                clean_text = re.sub('<[^<]+?>', '', html_text)
                clean_text = ' '.join(clean_text.split())
                
                title_match = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
                title = title_match.group(1) if title_match else url.split('/')[-1]
                
                self._store_web_content(url, title, clean_text)
                return clean_text[:5000]
        except Exception as e:
            return f"Error fetching web content: {str(e)}"
    
    def _store_web_content(self, url: str, title: str, content: str):
        """Store web content locally - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO web_sources (url, title, fetched_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (url, title))
        
        cursor.execute("""
            UPDATE web_sources 
            SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
            WHERE url = ?
        """, (url,))
        
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        cursor.execute("SELECT id FROM web_content WHERE content_hash = ?", (content_hash,))
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute("""
                INSERT INTO web_content (source_url, content, content_hash, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (url, content[:10000], content_hash))
            
            content_id = cursor.lastrowid
            
            words = set(content.lower().split())
            for word in list(words)[:30]:
                if len(word) > 3:
                    cursor.execute("""
                        INSERT INTO web_keywords (keyword, content_id)
                        VALUES (?, ?)
                    """, (word, content_id))
            
            self.data_ingestion.learn_from_text(
                f"Web content from {url}: {content[:500]}...",
                category="web",
                importance=2
            )
        
        conn.commit()
        conn.close()
    
    def search_web_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Search web knowledge locally - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords = query.lower().split()
        
        if keywords:
            keyword_conditions = []
            params = []
            
            for kw in keywords:
                if len(kw) > 2:
                    keyword_conditions.append("wk.keyword LIKE ?")
                    params.append(f"%{kw}%")
            
            if keyword_conditions:
                sql = f"""
                    SELECT DISTINCT wc.content, wc.importance, ws.url, ws.title
                    FROM web_content wc
                    JOIN web_keywords wk ON wc.id = wk.content_id
                    JOIN web_sources ws ON wc.source_url = ws.url
                    WHERE {' OR '.join(keyword_conditions)}
                    ORDER BY wc.importance DESC, ws.access_count DESC
                    LIMIT ?
                """
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            else:
                cursor.execute("""
                    SELECT wc.content, wc.importance, ws.url, ws.title
                    FROM web_content wc
                    JOIN web_sources ws ON wc.source_url = ws.url
                    WHERE wc.content LIKE ?
                    ORDER BY wc.importance DESC, ws.access_count DESC
                    LIMIT ?
                """, (f"%{query}%", limit))
                rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT wc.content, wc.importance, ws.url, ws.title
                FROM web_content wc
                JOIN web_sources ws ON wc.source_url = ws.url
                ORDER BY wc.created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
        
        conn.close()
        
        results = []
        for content, importance, url, title in rows:
            results.append({
                "content": content[:500] + "..." if len(content) > 500 else content,
                "importance": importance,
                "url": url,
                "title": title or url
            })
        
        return results
    
    def learn_from_url(self, url: str, category: str = "web") -> Dict:
        """Fetch and learn from a URL - 0 API calls"""
        content = self.fetch_url(url)
        
        if "Error" in content:
            return {"success": False, "message": content}
        
        learn_result = self.data_ingestion.learn_from_text(
            f"Web learning from {url}: {content[:1000]}",
            category=category,
            importance=2
        )
        
        return {
            "success": True,
            "url": url,
            "content_length": len(content),
            "chunks_learned": learn_result.get("count", 0)
        }
    
    def search_web_and_learn(self, topic: str) -> Dict:
        """Search the web and learn about a topic - 0 API calls"""
        encoded_query = urllib.parse.quote_plus(topic)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        content = self.fetch_url(search_url)
        
        if "Error" in content:
            return {"success": False, "message": content}
        
        learn_result = self.data_ingestion.learn_from_text(
            f"Learning about '{topic}' from web: {content[:1000]}",
            category="web_learning",
            importance=3
        )
        
        return {
            "success": True,
            "topic": topic,
            "content_length": len(content),
            "chunks_learned": learn_result.get("count", 0),
            "message": f"Ruby learned about '{topic}' from the web!"
        }
    
    def get_web_stats(self) -> Dict:
        """Get web learning statistics - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM web_sources")
        total_sources = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM web_content")
        total_content = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM web_content WHERE learned = 1")
        learned_content = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sources": total_sources,
            "total_content": total_content,
            "learned_content": learned_content,
            "learning_rate": (learned_content / total_content * 100) if total_content > 0 else 0
        }
