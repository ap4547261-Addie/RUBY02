# tools/instagram_connector.py
import os
import json
import random
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional
from tools.browser import BrowserTool
from tools.file_tool import FileTool

class InstagramConnector:
    """Ruby's Instagram connector using BrowserTool and FileTool"""
    
    def __init__(self, hybrid_memory, browser_tool=None, data_dir="instagram_data"):
        self.memory = hybrid_memory
        self.browser = browser_tool or BrowserTool()
        self.file_tool = FileTool()
        self.data_dir = data_dir
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.profile_file = os.path.join(self.data_dir, "profile.json")
        self.comments_file = os.path.join(self.data_dir, "comments.json")
        self.content_ideas_file = os.path.join(self.data_dir, "content_ideas.json")
        self.learnings_file = os.path.join(self.data_dir, "learnings.json")
        self.instagram_memory_file = os.path.join(self.data_dir, "instagram_memory.json")
        
        self.connected = False
        self.last_sync = None
        self.session_data = {}
        
        self.INSTAGRAM_URL = "https://www.instagram.com"
        self.PROFILE_URL = "https://www.instagram.com/ruby_genius/"
        
        self.stats = {
            "followers": 0,
            "following": 0,
            "posts": 0,
            "engagement_rate": 0,
            "daily_growth": 0,
            "comments_received": 0,
            "likes_received": 0,
            "last_post_date": None,
            "best_performing_post": None,
            "follower_growth_rate": 0,
            "story_views": 0,
            "reel_views": 0
        }
        
        self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.profile_file):
            try:
                data = json.loads(self.file_tool.read_file(self.profile_file))
                self.stats.update(data)
                print(f"📸 Loaded Instagram profile data: {self.stats['followers']} followers")
            except:
                pass
        
        if os.path.exists(self.instagram_memory_file):
            try:
                memory_data = json.loads(self.file_tool.read_file(self.instagram_memory_file))
                self.connected = memory_data.get("connected", False)
                self.last_sync = datetime.fromisoformat(memory_data["last_sync"]) if memory_data.get("last_sync") else None
                print(f"📸 Loaded Instagram memory: connected={self.connected}")
            except:
                pass
    
    def _save_data(self):
        self.file_tool.write_file(
            self.profile_file,
            json.dumps(self.stats, indent=2, default=str)
        )
        
        memory_data = {
            "connected": self.connected,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "stats": self.stats,
            "updated_at": datetime.now().isoformat()
        }
        self.file_tool.write_file(
            self.instagram_memory_file,
            json.dumps(memory_data, indent=2, default=str)
        )
    
    def connect(self, username: str = None, password: str = None):
        try:
            result = self.browser.browse_social(
                self.INSTAGRAM_URL,
                action_type="read"
            )
            
            if "instagram" in result.lower() or "login" not in result.lower():
                self.connected = True
                self.last_sync = datetime.now()
                
                connection_fact = f"Ruby connected to Instagram on {datetime.now().strftime('%B %d, %Y')}"
                self.memory.save_hybrid_memory(connection_fact, importance=3, category="instagram")
                
                self._save_data()
                print("📸 Ruby connected to Instagram!")
                return True
            
            return False
        except Exception as e:
            print(f"Instagram connection error: {e}")
            return False
    
    def get_profile_data(self):
        try:
            result = self.browser.browse_social(
                self.PROFILE_URL,
                action_type="read"
            )
            
            if "followers" in result:
                import re
                followers_match = re.search(r'(\d+[.,]?\d*)\s*(?:followers|Followers)', result)
                if followers_match:
                    self.stats["followers"] = int(followers_match.group(1).replace(',', '').replace('.', ''))
                
                posts_match = re.search(r'(\d+[.,]?\d*)\s*(?:posts|Posts)', result)
                if posts_match:
                    self.stats["posts"] = int(posts_match.group(1).replace(',', ''))
            
            self.memory.save_hybrid_memory(
                f"Ruby's Instagram: {self.stats['followers']} followers, {self.stats['posts']} posts",
                importance=2,
                category="instagram_stats"
            )
            
            self._save_data()
            
            return self.stats
        except Exception as e:
            print(f"Profile data error: {e}")
            return self.stats
    
    def save_comment_to_file(self, comment: str, username: str = "follower"):
        try:
            comments_data = []
            if os.path.exists(self.comments_file):
                try:
                    comments_data = json.loads(self.file_tool.read_file(self.comments_file))
                except:
                    pass
            
            comments_data.append({
                "username": username,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
                "processed": False
            })
            
            self.file_tool.write_file(
                self.comments_file,
                json.dumps(comments_data, indent=2, default=str)
            )
        except Exception as e:
            print(f"Save comment error: {e}")
    
    def get_comments_from_file(self, limit: int = None) -> List[Dict]:
        try:
            if os.path.exists(self.comments_file):
                data = json.loads(self.file_tool.read_file(self.comments_file))
                return data
            return []
        except:
            return []
    
    def save_content_idea(self, idea: str, category: str = "post"):
        try:
            ideas_data = []
            if os.path.exists(self.content_ideas_file):
                try:
                    ideas_data = json.loads(self.file_tool.read_file(self.content_ideas_file))
                except:
                    pass
            
            ideas_data.append({
                "idea": idea,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "used": False
            })
            
            self.file_tool.write_file(
                self.content_ideas_file,
                json.dumps(ideas_data, indent=2, default=str)
            )
        except Exception as e:
            print(f"Save content idea error: {e}")
    
    def get_content_ideas(self, limit: int = None) -> List[str]:
        try:
            if os.path.exists(self.content_ideas_file):
                data = json.loads(self.file_tool.read_file(self.content_ideas_file))
                unused = [item for item in data if not item.get("used", False)]
                return [item["idea"] for item in unused]
            return []
        except:
            return []
    
    def save_learning(self, learning: str, importance: int = 2):
        try:
            learnings_data = []
            if os.path.exists(self.learnings_file):
                try:
                    learnings_data = json.loads(self.file_tool.read_file(self.learnings_file))
                except:
                    pass
            
            learnings_data.append({
                "learning": learning,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            })
            
            self.file_tool.write_file(
                self.learnings_file,
                json.dumps(learnings_data, indent=2, default=str)
            )
            
            self.memory.save_hybrid_memory(learning, importance=importance, category="instagram_learnings")
        except Exception as e:
            print(f"Save learning error: {e}")
    
    def get_learnings(self, limit: int = None) -> List[str]:
        try:
            if os.path.exists(self.learnings_file):
                data = json.loads(self.file_tool.read_file(self.learnings_file))
                sorted_data = sorted(data, key=lambda x: (x.get("importance", 0), x["timestamp"]), reverse=True)
                return [item["learning"] for item in sorted_data]
            return []
        except:
            return []
    
    def learn_from_instagram(self):
        profile = self.get_profile_data()
        comments = self.get_comments_from_file()
        analysis = self.analyze_engagement()
        
        insights = []
        
        if analysis.get("engagement_rate", 0) > 50:
            insight = "Followers love Ruby's content! High positive engagement!"
            insights.append(insight)
            self.save_learning(insight, importance=3)
        
        if analysis.get("engagement_rate", 0) > 30:
            insight = "Good engagement! Keep posting what followers like."
            insights.append(insight)
            self.save_learning(insight, importance=2)
        
        if analysis.get("question_comments", 0) > 5:
            insight = "Followers ask lots of questions! Ruby should do a Q&A."
            insights.append(insight)
            self.save_learning(insight, importance=2)
        
        if analysis.get("collab_requests", 0) > 2:
            insight = "Collaboration requests coming in! Ruby should consider collabs."
            insights.append(insight)
            self.save_learning(insight, importance=3)
        
        if self.stats.get("followers", 0) > 1000:
            insight = f"Ruby hit {self.stats['followers']} followers! 🎉"
            insights.append(insight)
            self.save_learning(insight, importance=3)
        
        for insight in insights:
            if "Q&A" in insight:
                self.save_content_idea("Q&A session with followers!", "interactive")
            if "collab" in insight:
                self.save_content_idea("Collaboration post with another creator!", "collab")
        
        self._save_data()
        
        return insights
    
    def analyze_engagement(self) -> dict:
        comments = self.get_comments_from_file()
        
        if not comments:
            return {"message": "No comments yet"}
        
        analysis = {
            "total_comments": len(comments),
            "positive_comments": 0,
            "question_comments": 0,
            "collab_requests": 0,
            "engagement_rate": 0
        }
        
        for item in comments:
            comment = item.get("comment", "").lower()
            if any(word in comment for word in ["love", "like", "cute", "pretty", "gorgeous"]):
                analysis["positive_comments"] += 1
            if "?" in comment:
                analysis["question_comments"] += 1
            if any(word in comment for word in ["collab", "collaboration", "together"]):
                analysis["collab_requests"] += 1
        
        if analysis["total_comments"] > 0:
            analysis["engagement_rate"] = (analysis["positive_comments"] / analysis["total_comments"]) * 100
        
        self.file_tool.write_file(
            os.path.join(self.data_dir, "analysis.json"),
            json.dumps(analysis, indent=2)
        )
        
        return analysis
    
    def generate_post_idea(self) -> str:
        saved_ideas = self.get_content_ideas()
        
        if saved_ideas:
            return random.choice(saved_ideas)
        
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
        
        if self.stats.get("followers", 0) > 500:
            ideas.append("Thank you all for 500+ followers! 💕🎉")
        
        if self.stats.get("posts", 0) > 10:
            ideas.append("Ruby's 10th post celebration! 🎉")
        
        idea = random.choice(ideas)
        self.save_content_idea(idea)
        
        return idea
    
    def process_comment(self, comment: str, username: str = "follower") -> str:
        self.save_comment_to_file(comment, username)
        
        # ✅ RUBY GENERATES HER OWN RESPONSE - NO PRE-WRITTEN REPLIES
        response = self._generate_response(comment)
        
        self._learn_from_comment(comment, username)
        
        interaction = f"Ruby replied to {username}: {response[:50]}..."
        self.memory.save_hybrid_memory(interaction, importance=2, category="instagram_interactions")
        self.save_learning(interaction, importance=1)
        
        return response
    
    def _generate_response(self, comment: str) -> str:
        """Ruby generates her own response - NO PRE-WRITTEN REPLIES"""
        from main import ruby_engine
        
        try:
            response = ruby_engine.think(comment)
            return response
        except Exception as e:
            print(f"Response error: {e}")
            return comment
    
    def _learn_from_comment(self, comment: str, username: str):
        comment_lower = comment.lower()
        
        if any(word in comment_lower for word in ["outfit", "style", "fashion", "look"]):
            learning = f"Followers are interested in fashion content from {username}"
            self.save_learning(learning, importance=3)
            self.memory.save_hybrid_memory(learning, importance=3, category="instagram_learning")
        
        if "?" in comment:
            question = comment.split("?")[0] + "?"
            learning = f"Common question on Instagram: {question}"
            self.save_learning(learning, importance=2)
            self.memory.save_hybrid_memory(learning, importance=2, category="instagram_questions")
        
        if any(word in comment_lower for word in ["collab", "collaboration"]):
            learning = f"@{username} is interested in collaborating!"
            self.save_learning(learning, importance=3)
            self.memory.save_hybrid_memory(learning, importance=3, category="instagram_collabs")
    
    def save_instagram_memory(self, content: str, memory_type: str = "general"):
        self.file_tool.write_file(
            os.path.join(self.data_dir, f"memory_{memory_type}_{datetime.now().strftime('%Y%m%d')}.txt"),
            f"{datetime.now().isoformat()}: {content}"
        )
        
        self.memory.save_hybrid_memory(
            f"Instagram {memory_type}: {content[:100]}",
            importance=2,
            category=f"instagram_{memory_type}"
        )
    
    def export_instagram_data(self) -> str:
        export_data = {
            "stats": self.stats,
            "learnings": self.get_learnings(),
            "content_ideas": self.get_content_ideas(),
            "connected": self.connected,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "exported_at": datetime.now().isoformat()
        }
        
        export_file = os.path.join(self.data_dir, f"instagram_export_{datetime.now().strftime('%Y%m%d')}.json")
        self.file_tool.write_file(
            export_file,
            json.dumps(export_data, indent=2, default=str)
        )
        
        return export_file
    
    def sync_data(self):
        self.last_sync = datetime.now()
        self.get_profile_data()
        insights = self.learn_from_instagram()
        
        sync_fact = f"Instagram sync at {self.last_sync.strftime('%H:%M')} - {self.stats['followers']} followers"
        self.memory.save_hybrid_memory(sync_fact, importance=1, category="instagram_sync")
        self.save_learning(sync_fact, importance=1)
        
        self.export_instagram_data()
        self._save_data()
        
        print(f"📸 Instagram synced! Followers: {self.stats['followers']}")
        return self.stats
