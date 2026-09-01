# tools/websocket_handler.py - NEW FILE
import json
import threading
import asyncio
from datetime import datetime
from tools.data_ingestion import DataIngestion
from tools.web_learner import WebLearner
from tools.video_learner import VideoLearner
from tools.instagram_connector import InstagramConnector

class WebSocketHandler:
    """
    Handles WebSocket messages from browser extension
    Routes content to Ruby's learning systems
    """
    
    def __init__(self, hybrid_memory, data_ingestion, web_learner, video_learner, instagram_connector):
        self.memory = hybrid_memory
        self.data_ingestion = data_ingestion
        self.web_learner = web_learner
        self.video_learner = video_learner
        self.instagram_connector = instagram_connector
        
        self.message_count = 0
        print("🔌 WebSocketHandler initialized - Ruby can receive data from browser!")
    
    async def handle_message(self, message: dict):
        """
        Process messages from browser extension
        """
        self.message_count += 1
        platform = message.get("platform", "unknown")
        content = message.get("content", "")
        
        print(f"📨 Received message #{self.message_count} from {platform}")
        
        # Route based on platform
        if "instagram" in platform.lower():
            await self._handle_instagram_content(content)
        elif "youtube" in platform.lower() or "video" in platform.lower():
            await self._handle_video_content(content)
        elif "duckduckgo" in platform.lower() or "search" in platform.lower():
            await self._handle_search_content(content)
        else:
            await self._handle_general_content(content, platform)
        
        # Store in memory
        self.memory.save_hybrid_memory(
            f"Received data from {platform} at {datetime.now().strftime('%H:%M')}",
            importance=2,
            category="browser_extension"
        )
    
    async def _handle_instagram_content(self, content: str):
        """Process Instagram content"""
        # Extract useful information
        lines = content.split('\n')
        for line in lines[:10]:  # Process first 10 lines
            if line.strip():
                self.memory.save_hybrid_memory(
                    f"Instagram content: {line[:100]}",
                    importance=2,
                    category="instagram_web"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Instagram data from browser: {content[:500]}",
            category="instagram_web",
            importance=2
        )
    
    async def _handle_video_content(self, content: str):
        """Process video content (YouTube)"""
        # Extract video titles or metadata
        import re
        video_titles = re.findall(r'"title":"([^"]+)"', content)
        
        for title in video_titles[:3]:
            self.memory.save_hybrid_memory(
                f"Video found: {title}",
                importance=2,
                category="video_web"
            )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Video content from browser: {content[:500]}",
            category="video_web",
            importance=2
        )
    
    async def _handle_search_content(self, content: str):
        """Process search results"""
        # Extract search results
        import re
        results = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', content)
        
        for url, title in results[:5]:
            if 'youtube.com' in url:
                self.video_learner.get_video_metadata(url)
            else:
                self.memory.save_hybrid_memory(
                    f"Search result: {title[:50]}",
                    importance=1,
                    category="search_web"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Search results from browser: {content[:500]}",
            category="search_web",
            importance=2
        )
    
    async def _handle_general_content(self, content: str, platform: str):
        """Process general web content"""
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Web content from {platform}: {content[:500]}",
            category="web_content",
            importance=2
        )
        
        # Store in memory
        self.memory.save_hybrid_memory(
            f"Learned from {platform}: {content[:100]}...",
            importance=2,
            category="web_learning"
        )
    
    def get_stats(self) -> dict:
        """Get handler statistics"""
        return {
            "total_messages": self.message_count,
            "last_message": datetime.now().isoformat()
        }
