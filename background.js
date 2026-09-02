# tools/websocket_handler.py - Complete WebSocket Handler
import json
import threading
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List

class WebSocketHandler:
    """
    Handles WebSocket messages from browser extension
    Routes content to Ruby's learning systems
    All processing is LOCAL - 0 API calls
    """
    
    def __init__(self, hybrid_memory, data_ingestion, web_learner, video_learner, instagram_connector):
        self.memory = hybrid_memory
        self.data_ingestion = data_ingestion
        self.web_learner = web_learner
        self.video_learner = video_learner
        self.instagram_connector = instagram_connector
        
        self.message_count = 0
        self.platform_counts = {}
        self.start_time = datetime.now()
        
        print("🔌 WebSocketHandler initialized - Ruby can receive data from browser!")
        print("📡 Listening for messages from social media and web pages")
    
    async def handle_message(self, message: Dict[str, Any]):
        """
        Process messages from browser extension
        Routes based on platform and content type
        """
        self.message_count += 1
        platform = message.get("platform", "unknown").lower()
        content = message.get("content", "")
        url = message.get("url", "")
        timestamp = message.get("timestamp", datetime.now().isoformat())
        
        # Track platform counts
        self.platform_counts[platform] = self.platform_counts.get(platform, 0) + 1
        
        print(f"📨 Received message #{self.message_count} from {platform}")
        print(f"   Content length: {len(content)} chars")
        print(f"   URL: {url[:100]}..." if url else "   URL: None")
        
        # Route based on platform
        if platform in ["instagram", "social_instagram"]:
            await self._handle_instagram_content(content, url)
        elif platform in ["youtube", "video_youtube"]:
            await self._handle_video_content(content, url)
        elif platform in ["reddit", "social_reddit"]:
            await self._handle_reddit_content(content, url)
        elif platform in ["twitter", "x", "social_twitter"]:
            await self._handle_twitter_content(content, url)
        elif platform in ["linkedin", "social_linkedin"]:
            await self._handle_linkedin_content(content, url)
        elif platform in ["facebook", "social_facebook"]:
            await self._handle_facebook_content(content, url)
        elif platform in ["tiktok", "social_tiktok"]:
            await self._handle_tiktok_content(content, url)
        elif platform in ["pinterest", "social_pinterest"]:
            await self._handle_pinterest_content(content, url)
        elif "search" in platform or "duckduckgo" in platform:
            await self._handle_search_content(content, url)
        else:
            await self._handle_general_content(content, platform, url)
        
        # Store in hybrid memory
        self.memory.save_hybrid_memory(
            f"Received {len(content)} chars from {platform} at {datetime.now().strftime('%H:%M')}",
            importance=2,
            category="browser_extension"
        )
    
    async def _handle_instagram_content(self, content: str, url: str = ""):
        """Process Instagram content - 0 API calls - NO LIMIT"""
        print("📸 Processing Instagram content...")
        
        # Extract profile info
        profile_match = re.search(r'Profile:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if profile_match:
            profile = profile_match.group(1).strip()
            self.memory.save_hybrid_memory(
                f"Instagram profile: {profile}",
                importance=2,
                category="instagram_profile"
            )
        
        # Extract posts - NO LIMIT
        posts = re.findall(r'Post \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for post in posts:
            if post.strip():
                self.memory.save_hybrid_memory(
                    f"Instagram post: {post[:200]}",
                    importance=2,
                    category="instagram_posts"
                )
        
        # Extract comments - NO LIMIT
        comments = re.findall(r'Comment \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for comment in comments:
            if comment.strip():
                self.memory.save_hybrid_memory(
                    f"Instagram comment: {comment[:200]}",
                    importance=1,
                    category="instagram_comments"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Instagram data from browser: {content[:500]}",
            category="instagram_web",
            importance=2
        )
        
        print(f"📸 Learned from Instagram: {len(posts)} posts, {len(comments)} comments")
    
    async def _handle_video_content(self, content: str, url: str = ""):
        """Process YouTube/video content - 0 API calls - NO LIMIT"""
        print("🎬 Processing YouTube content...")
        
        # Extract video title
        title_match = re.search(r'Video:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            self.memory.save_hybrid_memory(
                f"YouTube video: {title}",
                importance=3,
                category="video_metadata"
            )
            
            # If video learner is available
            if self.video_learner and url:
                self.video_learner.get_video_metadata(url)
        
        # Extract channel
        channel_match = re.search(r'Channel:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if channel_match:
            channel = channel_match.group(1).strip()
            self.memory.save_hybrid_memory(
                f"YouTube channel: {channel}",
                importance=2,
                category="video_channel"
            )
        
        # Extract comments - NO LIMIT
        comments = re.findall(r'Comment \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for comment in comments:
            if comment.strip():
                self.memory.save_hybrid_memory(
                    f"YouTube comment: {comment[:200]}",
                    importance=1,
                    category="video_comments"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Video content from browser: {content[:500]}",
            category="video_web",
            importance=2
        )
        
        print(f"🎬 Learned from YouTube: {len(comments)} comments")
    
    async def _handle_reddit_content(self, content: str, url: str = ""):
        """Process Reddit content - 0 API calls - NO LIMIT"""
        print("📚 Processing Reddit content...")
        
        # Extract posts - NO LIMIT
        posts = re.findall(r'Post \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for post in posts:
            if post.strip():
                self.memory.save_hybrid_memory(
                    f"Reddit post: {post[:200]}",
                    importance=2,
                    category="reddit_posts"
                )
        
        # Extract comments - NO LIMIT
        comments = re.findall(r'Comment \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for comment in comments:
            if comment.strip():
                self.memory.save_hybrid_memory(
                    f"Reddit comment: {comment[:200]}",
                    importance=1,
                    category="reddit_comments"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Reddit data from browser: {content[:500]}",
            category="reddit_web",
            importance=2
        )
        
        print(f"📚 Learned from Reddit: {len(posts)} posts, {len(comments)} comments")
    
    async def _handle_twitter_content(self, content: str, url: str = ""):
        """Process Twitter/X content - 0 API calls - NO LIMIT"""
        print("🐦 Processing Twitter content...")
        
        # Extract tweets - NO LIMIT
        tweets = re.findall(r'Tweet \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for tweet in tweets:
            if tweet.strip():
                self.memory.save_hybrid_memory(
                    f"Tweet: {tweet[:200]}",
                    importance=2,
                    category="twitter_tweets"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Twitter data from browser: {content[:500]}",
            category="twitter_web",
            importance=2
        )
        
        print(f"🐦 Learned from Twitter: {len(tweets)} tweets")
    
    async def _handle_linkedin_content(self, content: str, url: str = ""):
        """Process LinkedIn content - 0 API calls - NO LIMIT"""
        print("💼 Processing LinkedIn content...")
        
        # Extract posts - NO LIMIT
        posts = re.findall(r'Post \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for post in posts:
            if post.strip():
                self.memory.save_hybrid_memory(
                    f"LinkedIn post: {post[:200]}",
                    importance=2,
                    category="linkedin_posts"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"LinkedIn data from browser: {content[:500]}",
            category="linkedin_web",
            importance=2
        )
        
        print(f"💼 Learned from LinkedIn: {len(posts)} posts")
    
    async def _handle_facebook_content(self, content: str, url: str = ""):
        """Process Facebook content - 0 API calls - NO LIMIT"""
        print("📘 Processing Facebook content...")
        
        # Extract posts - NO LIMIT
        posts = re.findall(r'Post \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for post in posts:
            if post.strip():
                self.memory.save_hybrid_memory(
                    f"Facebook post: {post[:200]}",
                    importance=2,
                    category="facebook_posts"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Facebook data from browser: {content[:500]}",
            category="facebook_web",
            importance=2
        )
        
        print(f"📘 Learned from Facebook: {len(posts)} posts")
    
    async def _handle_tiktok_content(self, content: str, url: str = ""):
        """Process TikTok content - 0 API calls - NO LIMIT"""
        print("🎵 Processing TikTok content...")
        
        # Extract videos - NO LIMIT
        videos = re.findall(r'Video \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for video in videos:
            if video.strip():
                self.memory.save_hybrid_memory(
                    f"TikTok video: {video[:200]}",
                    importance=2,
                    category="tiktok_videos"
                )
        
        # Extract comments - NO LIMIT
        comments = re.findall(r'Comment \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for comment in comments:
            if comment.strip():
                self.memory.save_hybrid_memory(
                    f"TikTok comment: {comment[:200]}",
                    importance=1,
                    category="tiktok_comments"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"TikTok data from browser: {content[:500]}",
            category="tiktok_web",
            importance=2
        )
        
        print(f"🎵 Learned from TikTok: {len(videos)} videos, {len(comments)} comments")
    
    async def _handle_pinterest_content(self, content: str, url: str = ""):
        """Process Pinterest content - 0 API calls - NO LIMIT"""
        print("📌 Processing Pinterest content...")
        
        # Extract pins - NO LIMIT
        pins = re.findall(r'Pin \d+:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        for pin in pins:
            if pin.strip():
                self.memory.save_hybrid_memory(
                    f"Pinterest pin: {pin[:200]}",
                    importance=2,
                    category="pinterest_pins"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Pinterest data from browser: {content[:500]}",
            category="pinterest_web",
            importance=2
        )
        
        print(f"📌 Learned from Pinterest: {len(pins)} pins")
    
    async def _handle_search_content(self, content: str, url: str = ""):
        """Process search results - 0 API calls - NO LIMIT"""
        print("🔍 Processing search content...")
        
        # Extract search results - NO LIMIT
        results = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', content)
        
        for url, title in results:
            if 'youtube.com' in url:
                if self.video_learner:
                    self.video_learner.get_video_metadata(url)
            else:
                self.memory.save_hybrid_memory(
                    f"Search result: {title[:100]}",
                    importance=1,
                    category="search_results"
                )
        
        # Learn from content
        self.data_ingestion.learn_from_text(
            f"Search results from browser: {content[:500]}",
            category="search_web",
            importance=2
        )
        
        print(f"🔍 Learned from search: {len(results)} results")
    
    async def _handle_general_content(self, content: str, platform: str, url: str = ""):
        """Process general web content - 0 API calls"""
        print(f"🌐 Processing general content from {platform}")
        
        # Extract title
        title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            self.memory.save_hybrid_memory(
                f"Page title: {title[:100]}",
                importance=2,
                category="web_pages"
            )
        
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
        
        print(f"🌐 Learned general content: {len(content)} chars")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            "total_messages": self.message_count,
            "platform_counts": self.platform_counts,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "last_message": datetime.now().isoformat()
        }
    
    def get_platform_summary(self) -> str:
        """Get human-readable platform summary"""
        if not self.platform_counts:
            return "No data received yet"
        
        summary = "📊 Platform Summary:\n"
        for platform, count in sorted(self.platform_counts.items(), key=lambda x: x[1], reverse=True):
            emoji = {
                'instagram': '📸',
                'youtube': '🎬',
                'reddit': '📚',
                'twitter': '🐦',
                'linkedin': '💼',
                'facebook': '📘',
                'tiktok': '🎵',
                'pinterest': '📌'
            }.get(platform, '🌐')
            summary += f"  {emoji} {platform}: {count} messages\n"
        
        return summary
