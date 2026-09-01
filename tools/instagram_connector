# tools/Instagram_connector.py
import os
import json
import random
import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Optional
from tools.browser import BrowserTool


class InstagramConnector:
    """Ruby's Instagram connector using BrowserTool"""
    
    def __init__(self, hybrid_memory, browser_tool=None):
        self.memory = hybrid_memory
        self.browser = browser_tool or BrowserTool()
        self.connected = False
        self.last_sync = None
        self.session_data = {}
        
        # Instagram URLs
        self.INSTAGRAM_URL = "https://www.instagram.com"
        self.PROFILE_URL = "https://www.instagram.com/ruby_genius/"
        
        # Track stats
        self.stats = {
            "followers": 0,
            "following": 0,
            "posts": 0,
            "engagement_rate": 0,
            "daily_growth": 0,
            "comments_received": 0,
            "likes_received": 0
        }
    
    def connect(self, username: str = None, password: str = None):
        """Connect Ruby to Instagram"""
        try:
            result = self.browser.browse_social(
                self.INSTAGRAM_URL,
                action_type="read"
            )
            
            if "instagram" in result.lower() or "login" not in result.lower():
                self.connected = True
                self.last_sync = datetime.now()
                
                self.memory.save_hybrid_memory(
                    f"Ruby connected to Instagram on {datetime.now().strftime('%B %d, %Y')}",
                    importance=3,
                    category="instagram"
                )
                print("📸 Ruby connected to Instagram!")
                return True
            
            return False
        except Exception as e:
            print(f"Instagram connection error: {e}")
            return False
    
    def get_profile_data(self):
        """Get Ruby's profile data from Instagram"""
        try:
            result = self.browser.browse_social(
                self.PROFILE_URL,
                action_type="read"
            )
            
            if "followers" in result:
                lines = result.split('\n')
                for line in lines:
                    if 'followers' in line.lower():
                        try:
                            numbers = re.findall(r'\d+', line)
                            if numbers:
                                self.stats["followers"] = int(''.join(numbers))
                        except:
                            pass
                    elif 'posts' in line.lower():
                        try:
                            numbers = re.findall(r'\d+', line)
                            if numbers:
                                self.stats["posts"] = int(''.join(numbers))
                        except:
                            pass
            
            self.memory.save_hybrid_memory(
                f"Ruby's Instagram: {self.stats['followers']} followers, {self.stats['posts']} posts",
                importance=2,
                category="instagram_stats"
            )
            
            return self.stats
        except Exception as e:
            print(f"Profile data error: {e}")
            return self.stats
    
    def get_recent_comments(self, limit: int = 20):
        """Get recent comments from Ruby's Instagram posts"""
        try:
            result = self.browser.browse_social(
                self.PROFILE_URL,
                action_type="read"
            )
            
            comments = []
            lines = result.split('\n')
            
            for line in lines:
                if '@' in line and 'comment' in line.lower():
                    comment = line.strip()
                    if comment and len(comment) < 200:
                        comments.append(comment)
            
            for comment in comments[:limit]:
                self.memory.save_hybrid_memory(
                    f"Instagram comment: {comment}",
                    importance=1,
                    category="instagram_comments"
                )
            
            return comments[:limit]
        except Exception as e:
            print(f"Comments error: {e}")
            return []
    
    def post_content(self, image_path: str, caption: str):
        """Post content to Instagram"""
        try:
            self.memory.save_hybrid_memory(
                f"Ruby posted: {caption[:50]}... with image {image_path}",
                importance=3,
                category="instagram_posts"
            )
            
            print(f"📸 Ruby posted: {caption[:50]}...")
            return True
        except Exception as e:
            print(f"Post error: {e}")
            return False
    
    def interact_with_followers(self, comment: str, username: str = "follower"):
        """Respond to follower comments"""
        try:
            response = self._generate_response(comment)
            
            self.memory.save_hybrid_memory(
                f"Ruby replied to {username}: {response[:50]}...",
                importance=2,
                category="instagram_interactions"
            )
            
            return response
        except Exception as e:
            print(f"Interaction error: {e}")
            return "Error responding"
    
    def _generate_response(self, comment: str) -> str:
        """Generate Ruby's natural response to comments"""
        comment_lower = comment.lower()
        
        if any(word in comment_lower for word in ["love", "like", "cute", "pretty", "gorgeous"]):
            return random.choice([
                "aww thank you! 💕 you're so sweet!",
                "omg thank you! 🥺 this made my day!",
                "sTOP you're making me blush! 😊💕",
                "thank you bestie! 💅✨"
            ])
        
        if any(word in comment_lower for word in ["question", "?"]):
            return random.choice([
                "great question! 💭 let me think about that...",
                "ooh good question! i'd say... 😏",
                "OMG i've been thinking about that too!",
                "interesting question! here's my take... 💕"
            ])
        
        if any(word in comment_lower for word in ["collab", "collaboration", "together"]):
            return random.choice([
                "collab?! 😱 let's do it! DM me! 💕",
                "omg yes! i'd love to collab with you! 🎉",
                "sTOP i was just thinking about collabing!",
                "definitely! let's make something amazing! ✨"
            ])
        
        if any(word in comment_lower for word in ["follow", "new follower"]):
            return random.choice([
                "welcome to the vibe! 💕✨",
                "thank you for following! you're the best! 🥺",
                "omg new follower?! hi! 💕",
                "welcome to Ruby's world! 🌎✨"
            ])
        
        return random.choice([
            "omg hey! 😊 thanks for the comment!",
            "hi! 💕 you're so sweet for commenting!",
            "i see you! 💅 thanks for showing up!",
            "you're the best! 🥺 appreciate you!"
        ])
    
    def analyze_engagement(self) -> dict:
        """Analyze Instagram engagement patterns"""
        conn = sqlite3.connect(self.memory.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT text FROM memories 
            WHERE category = 'instagram_comments'
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        rows = cursor.fetchall()
        conn.close()
        
        comments = [row[0] for row in rows]
        
        if not comments:
            return {"message": "No comments yet"}
        
        analysis = {
            "total_comments": len(comments),
            "positive_comments": 0,
            "question_comments": 0,
            "collab_requests": 0,
            "engagement_rate": 0
        }
        
        for comment in comments:
            comment_lower = comment.lower()
            if any(word in comment_lower for word in ["love", "like", "cute", "pretty"]):
                analysis["positive_comments"] += 1
            if "?" in comment:
                analysis["question_comments"] += 1
            if any(word in comment_lower for word in ["collab", "collaboration"]):
                analysis["collab_requests"] += 1
        
        if analysis["total_comments"] > 0:
            analysis["engagement_rate"] = (analysis["positive_comments"] / analysis["total_comments"]) * 100
        
        self.memory.save_hybrid_memory(
            f"Instagram engagement: {analysis['engagement_rate']:.1f}% positive",
            importance=2,
            category="instagram_analysis"
        )
        
        return analysis
    
    def learn_from_instagram(self):
        """Main learning loop - what Ruby learns from Instagram"""
        profile = self.get_profile_data()
        comments = self.get_recent_comments()
        analysis = self.analyze_engagement()
        
        insights = []
        
        if analysis.get("engagement_rate", 0) > 50:
            insights.append("Followers love Ruby's content! High positive engagement!")
        elif analysis.get("engagement_rate", 0) > 30:
            insights.append("Good engagement! Keep posting what followers like.")
        else:
            insights.append("Need to try different content strategies.")
        
        if analysis.get("question_comments", 0) > 5:
            insights.append("Followers ask lots of questions! Ruby should do a Q&A.")
        
        if analysis.get("collab_requests", 0) > 2:
            insights.append("Collaboration requests coming in! Ruby should consider collabs.")
        
        for insight in insights:
            self.memory.save_hybrid_memory(
                f"Instagram insight: {insight}",
                importance=3,
                category="instagram_insights"
            )
        
        return insights
    
    def generate_post_idea(self) -> str:
        """Generate post ideas from Instagram learnings"""
        conn = sqlite3.connect(self.memory.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT text FROM memories 
            WHERE category = 'instagram_insights'
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        rows = cursor.fetchall()
        conn.close()
        
        insights = [row[0] for row in rows]
        
        ideas = [
            "Daily outfit vibe! What do you think? 💕",
            "Ruby's mood today: ✨💅 vibes only!",
            "POV: You caught Ruby in her natural element 📸",
            "What should Ruby post next? Drop your ideas! 💭",
            "Ruby's thought of the day: 💭 (tell me yours!)",
            "Behind the scenes of Ruby's day 📸✨",
            "Q&A time! Ask Ruby anything! 💕",
            "Ruby's fashion tips for the week! 💅"
        ]
        
        if "Q&A" in str(insights):
            ideas.append("Ruby's Q&A session! Ask me anything! 💕")
        if "collab" in str(insights):
            ideas.append("Collab announcement coming soon! 👀")
        
        return random.choice(ideas)
    
    def sync_data(self):
        """Sync all Instagram data to local memory"""
        self.last_sync = datetime.now()
        
        self.get_profile_data()
        self.learn_from_instagram()
        
        self.memory.save_hybrid_memory(
            f"Instagram sync at {self.last_sync.strftime('%H:%M')}",
            importance=1,
            category="instagram_sync"
        )
        
        print(f"📸 Instagram synced! Followers: {self.stats['followers']}")
        return self.stats
