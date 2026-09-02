# tools/video_learner.py
import urllib.request
import urllib.parse
import json
import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Optional
from tools.data_ingestion import DataIngestion

class VideoLearner:
    """
    Ruby's Video Learning System - Learns from YouTube and other video platforms
    0 API calls for learning (uses local storage)
    """
    
    def __init__(self, data_ingestion: DataIngestion, db_path="ruby_video_knowledge.db"):
        self.data_ingestion = data_ingestion
        self.db_path = db_path
        self._init_db()
        print("🎬 VideoLearner initialized - Ruby can learn from videos!")
    
    def _init_db(self):
        """Initialize video knowledge database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE,
                title TEXT,
                author TEXT,
                url TEXT,
                platform TEXT DEFAULT 'youtube',
                watched BOOLEAN DEFAULT 0,
                learned_from BOOLEAN DEFAULT 0,
                watch_count INTEGER DEFAULT 0,
                last_watched TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Video learnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                learning TEXT,
                category TEXT DEFAULT 'video',
                importance INTEGER DEFAULT 2,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
        """)
        
        # Video categories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                category TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_video_metadata(self, video_url: str) -> Dict:
        """
        Fetch metadata from YouTube video - 0 API calls
        """
        try:
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Could not extract video ID"}
            
            # Use oEmbed
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(video_url)}&format=json"
            req = urllib.request.Request(oembed_url)
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                metadata = {
                    "video_id": video_id,
                    "title": data.get("title", "Unknown Title"),
                    "author": data.get("author_name", "Unknown Author"),
                    "platform": "youtube",
                    "url": video_url
                }
                
                # Store in database
                self._store_video_metadata(metadata)
                
                return metadata
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)',
            r'(?:youtube\.com\/v\/)([\w-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _store_video_metadata(self, metadata: Dict):
        """Store video metadata locally - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO videos (video_id, title, author, url, platform)
            VALUES (?, ?, ?, ?, ?)
        """, (
            metadata["video_id"],
            metadata["title"],
            metadata["author"],
            metadata["url"],
            metadata["platform"]
        ))
        
        conn.commit()
        conn.close()
    
    def learn_from_video(self, video_url: str, topic: str = None) -> Dict:
        """
        Learn from a video - 0 API calls
        """
        # Get metadata
        metadata = self.get_video_metadata(video_url)
        
        if "error" in metadata:
            return {"success": False, "message": metadata["error"]}
        
        # Learn from video metadata
        learning_text = f"""
        Ruby learned from video: {metadata['title']}
        Author: {metadata['author']}
        Topic: {topic or 'General'}
        """
        
        # Store learning in DataIngestion
        learn_result = self.data_ingestion.learn_from_text(
            learning_text,
            category="video",
            importance=3
        )
        
        # Store in video learnings
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO video_learnings (video_id, learning, category)
            VALUES (?, ?, ?)
        """, (
            metadata["video_id"],
            learning_text,
            "video"
        ))
        
        cursor.execute("""
            UPDATE videos 
            SET learned_from = 1, last_watched = CURRENT_TIMESTAMP, watch_count = watch_count + 1
            WHERE video_id = ?
        """, (metadata["video_id"],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "video_id": metadata["video_id"],
            "title": metadata["title"],
            "author": metadata["author"],
            "learned": True
        }
    
    def search_video_knowledge(self, query: str, limit: int = None) -> List[Dict]:
        """
        Search knowledge learned from videos - 0 API calls - NO LIMIT
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vl.learning, vl.category, v.title, v.author, v.video_id
            FROM video_learnings vl
            JOIN videos v ON vl.video_id = v.video_id
            WHERE vl.learning LIKE ? OR v.title LIKE ?
            ORDER BY vl.importance DESC, v.watch_count DESC
        """, (f"%{query}%", f"%{query}%"))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for learning, category, title, author, video_id in rows:
            results.append({
                "learning": learning[:300] + "..." if len(learning) > 300 else learning,
                "category": category,
                "video_title": title,
                "video_author": author,
                "video_id": video_id
            })
        
        return results
    
    def get_watched_videos(self, limit: int = None) -> List[Dict]:
        """Get recently watched videos - 0 API calls - NO LIMIT"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, author, url, watch_count, last_watched
            FROM videos
            WHERE watched = 1
            ORDER BY last_watched DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "title": row[0],
                "author": row[1],
                "url": row[2],
                "watch_count": row[3],
                "last_watched": row[4]
            }
            for row in rows
        ]
    
    def get_video_stats(self) -> Dict:
        """Get video learning statistics - 0 API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM videos")
        total_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos WHERE learned_from = 1")
        learned_videos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM video_learnings")
        total_learnings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_videos": total_videos,
            "learned_videos": learned_videos,
            "total_learnings": total_learnings,
            "learning_rate": (learned_videos / total_videos * 100) if total_videos > 0 else 0
        }
    
    def learn_from_youtube_search(self, query: str) -> Dict:
        """
        Search YouTube and learn from videos - 0 API calls
        """
        # Use DuckDuckGo search for YouTube videos
        encoded_query = urllib.parse.quote_plus(f"site:youtube.com {query}")
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        # Fetch search results
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            req = urllib.request.Request(search_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_text = response.read().decode('utf-8', errors='ignore')
                
                # Extract video links
                video_links = re.findall(r'href="(https?://www\.youtube\.com/watch\?v=[\w-]+)"', html_text)
                video_links = list(dict.fromkeys(video_links))
                
                learned = 0
                for link in video_links:
                    result = self.learn_from_video(link, query)
                    if result.get("success"):
                        learned += 1
                
                return {
                    "success": True,
                    "query": query,
                    "videos_found": len(video_links),
                    "videos_learned": learned,
                    "message": f"Ruby learned from {learned} videos about '{query}'!"
                }
        except Exception as e:
            return {"success": False, "message": f"Search error: {str(e)}"}
