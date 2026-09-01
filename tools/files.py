# tools/instagram_connector.py - Updated with FileTool
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
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Instagram files
        self.profile_file = os.path.join(self.data_dir, "profile.json")
        self.comments_file = os.path.join(self.data_dir, "comments.json")
        self.content_ideas_file = os.path.join(self.data_dir, "content_ideas.json")
        self.learnings_file = os.path.join(self.data_dir, "learnings.json")
        self.instagram_memory_file = os.path.join(self.data_dir, "instagram_memory.json")
        
        self.connected = False
        self.last_sync = None
        self.session_data = {}
        
        # Instagram URLs
        self.INSTAGRAM_URL = "https://www.instagram.com"
        self.PROFILE_URL = "https://www.instagram.com/ruby_genius/"  # Ruby's profile
        
        # Track stats
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
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load Instagram data from files"""
        # Load profile data
        if os.path.exists(self.profile_file):
            try:
                data = json.loads(self.file_tool.read_file(self.profile_file))
                self.stats.update(data)
                print(f"📸 Loaded Instagram profile data: {self.stats['followers']} followers")
            except:
                pass
        
        # Load Instagram memory
        if os.path.exists(self.instagram_memory_file):
            try:
                memory_data = json.loads(self.file_tool.read_file(self.instagram_memory_file))
                # Restore memory state
                self.connected = memory_data.get("connected", False)
                self.last_sync = datetime.fromisoformat(memory_data["last_sync"]) if memory_data.get("last_sync") else None
                print(f"📸 Loaded Instagram memory: connected={self.connected}")
            except:
                pass
    
    def _save_data(self):
        """Save Instagram data to files"""
        # Save profile data
        self.file_tool.write_file(
            self.profile_file,
            json.dumps(self.stats, indent=2, default=str)
        )
        
        # Save Instagram memory
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
        """Connect Ruby to Instagram"""
        try:
            # Check if already logged in via browser profile
            result = self.browser.browse_social(
                self.INSTAGRAM_URL,
                action_type="read"
            )
            
            # Check if we got Instagram content
            if "instagram" in result.lower() or "login" not in result.lower():
                self.connected = True
                self.last_sync = datetime.now()
                
                # Store connection in memory and file
                connection_fact = f"Ruby connected to Instagram on {datetime.now().strftime('%B %d, %Y')}"
                self.memory.save_hybrid_memory(connection_fact, importance=3, category="instagram")
                
                # Save connection data
                self._save_data()
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
            
            # Extract profile data
            if "followers" in result:
                import re
                # Extract followers count
                followers_match = re.search(r'(\d+[.,]?\d*)\s*(?:followers|Followers)', result)
                if followers_match:
                    self.stats["followers"] = int(followers_match.group(1).replace(',', '').replace('.', ''))
                
                # Extract posts count
                posts_match = re.search(r'(\d+[.,]?\d*)\s*(?:posts|Posts)', result)
                if posts_match:
                    self.stats["posts"] = int(posts_match.group(1).replace(',', ''))
            
            # Store in memory
            self.memory.save_hybrid_memory(
                f"Ruby's Instagram: {self.stats['followers']} followers, {self.stats['posts']} posts",
                importance=2,
                category="instagram_stats"
            )
            
            # Save to file
            self._save_data()
            
            return self.stats
        except Exception as e:
            print(f"Profile data error: {e}")
            return self.stats
    
    def save_comment_to_file(self, comment: str, username: str = "follower"):
        """Save Instagram comment to file for learning"""
        try:
            # Load existing comments
            comments_data = []
            if os.path.exists(self.comments_file):
                try:
                    comments_data = json.loads(self.file_tool.read_file(self.comments_file))
                except:
                    pass
            
            # Add new comment
            comments_data.append({
                "username": username,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
                "processed": False
            })
            
            # Save back
            self.file_tool.write_file(
                self.comments_file,
                json.dumps(comments_data, indent=2, default=str)
            )
        except Exception as e:
            print(f"Save comment error: {e}")
    
    def get_comments_from_file(self, limit: int = 20) -> List[Dict]:
        """Get comments from file for learning"""
        try:
            if os.path.exists(self.comments_file):
                data = json.loads(self.file_tool.read_file(self.comments_file))
                return data[-limit:]  # Return most recent
            return []
        except:
            return []
    
    def save_content_idea(self, idea: str, category: str = "post"):
        """Save content idea to file"""
        try:
            # Load existing ideas
            ideas_data = []
            if os.path.exists(self.content_ideas_file):
                try:
                    ideas_data = json.loads(self.file_tool.read_file(self.content_ideas_file))
                except:
                    pass
            
            # Add new idea
            ideas_data.append({
                "idea": idea,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "used": False
            })
            
            # Save back
            self.file_tool.write_file(
                self.content_ideas_file,
                json.dumps(ideas_data, indent=2, default=str)
            )
        except Exception as e:
            print(f"Save content idea error: {e}")
    
    def get_content_ideas(self, limit: int = 10) -> List[str]:
        """Get content ideas from file"""
        try:
            if os.path.exists(self.content_ideas_file):
                data = json.loads(self.file_tool.read_file(self.content_ideas_file))
                # Get unused ideas
                unused = [item for item in data if not item.get("used", False)]
                return [item["idea"] for item in unused[:limit]]
            return []
        except:
            return []
    
    def save_learning(self, learning: str, importance: int = 2):
        """Save a learning from Instagram"""
        try:
            # Load existing learnings
            learnings_data = []
            if os.path.exists(self.learnings_file):
                try:
                    learnings_data = json.loads(self.file_tool.read_file(self.learnings_file))
                except:
                    pass
            
            # Add new learning
            learnings_data.append({
                "learning": learning,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save back
            self.file_tool.write_file(
                self.learnings_file,
                json.dumps(learnings_data, indent=2, default=str)
            )
            
            # Also save to memory
            self.memory.save_hybrid_memory(learning, importance=importance, category="instagram_learnings")
        except Exception as e:
            print(f"Save learning error: {e}")
    
    def get_learnings(self, limit: int = 10) -> List[str]:
        """Get learnings from file"""
        try:
            if os.path.exists(self.learnings_file):
                data = json.loads(self.file_tool.read_file(self.learnings_file))
                # Sort by importance and recency
                sorted_data = sorted(data, key=lambda x: (x.get("importance", 0), x["timestamp"]), reverse=True)
                return [item["learning"] for item in sorted_data[:limit]]
            return []
        except:
            return []
    
    def learn_from_instagram(self):
        """Main learning loop - what Ruby learns from Instagram"""
        # Get profile data
        profile = self.get_profile_data()
        
        # Get recent comments
        comments = self.get_comments_from_file()
        
        # Analyze engagement
        analysis = self.analyze_engagement()
        
        # Generate and save insights
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
        
        # Save insights to content ideas
        for insight in insights:
            if "Q&A" in insight:
                self.save_content_idea("Q&A session with followers!", "interactive")
            if "collab" in insight:
                self.save_content_idea("Collaboration post with another creator!", "collab")
        
        # Save data
        self._save_data()
        
        return insights
    
    def analyze_engagement(self) -> dict:
        """Analyze Instagram engagement patterns"""
        comments = self.get_comments_from_file()
        
        if not comments:
            return {"message": "No comments yet"}
        
        # Analyze patterns
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
        
        # Store analysis in file
        self.file_tool.write_file(
            os.path.join(self.data_dir, "analysis.json"),
            json.dumps(analysis, indent=2)
        )
        
        return analysis
    
    def generate_post_idea(self) -> str:
        """Generate post ideas from Instagram learnings and files"""
        # Get ideas from file
        saved_ideas = self.get_content_ideas()
        
        if saved_ideas:
            return random.choice(saved_ideas)
        
        # Generate new ideas
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
        
        # Add some personalized ones
        if self.stats.get("followers", 0) > 500:
            ideas.append("Thank you all for 500+ followers! 💕🎉")
        
        if self.stats.get("posts", 0) > 10:
            ideas.append("Ruby's 10th post celebration! 🎉")
        
        idea = random.choice(ideas)
        
        # Save idea
        self.save_content_idea(idea)
        
        return idea
    
    def process_comment(self, comment: str, username: str = "follower") -> str:
        """Process a comment and generate Ruby's response"""
        # Save comment to file
        self.save_comment_to_file(comment, username)
        
        # Generate response
        response = self._generate_response(comment)
        
        # Learn from comment
        self._learn_from_comment(comment, username)
        
        # Save interaction
        interaction = f"Ruby replied to {username}: {response[:50]}..."
        self.memory.save_hybrid_memory(interaction, importance=2, category="instagram_interactions")
        self.save_learning(interaction, importance=1)
        
        return response
    
    def _generate_response(self, comment: str) -> str:
        """Generate Ruby's natural response to comments"""
        comment_lower = comment.lower()
        
        responses = {
            "love": [
                "aww thank you! 💕 you're so sweet!",
                "omg thank you! 🥺 this made my day!",
                "sTOP you're making me blush! 😊💕",
                "thank you bestie! 💅✨"
            ],
            "question": [
                "great question! 💭 let me think about that...",
                "ooh good question! i'd say... 😏",
                "OMG i've been thinking about that too!",
                "interesting question! here's my take... 💕"
            ],
            "collab": [
                "collab?! 😱 let's do it! DM me! 💕",
                "omg yes! i'd love to collab with you! 🎉",
                "sTOP i was just thinking about collabing!",
                "definitely! let's make something amazing! ✨"
            ],
            "follow": [
                "welcome to the vibe! 💕✨",
                "thank you for following! you're the best! 🥺",
                "omg new follower?! hi! 💕",
                "welcome to Ruby's world! 🌎✨"
            ]
        }
        
        # Match comment to response type
        if any(word in comment_lower for word in ["love", "like", "cute", "pretty", "gorgeous"]):
            return random.choice(responses["love"])
        if "?" in comment_lower:
            return random.choice(responses["question"])
        if any(word in comment_lower for word in ["collab", "collaboration", "together"]):
            return random.choice(responses["collab"])
        if any(word in comment_lower for word in ["follow", "new follower"]):
            return random.choice(responses["follow"])
        
        # Default responses
        default_responses = [
            "omg hey! 😊 thanks for the comment!",
            "hi! 💕 you're so sweet for commenting!",
            "i see you! 💅 thanks for showing up!",
            "you're the best! 🥺 appreciate you!",
            "omg i love your energy! 💕",
            "you're so nice! made my day! 🥺"
        ]
        return random.choice(default_responses)
    
    def _learn_from_comment(self, comment: str, username: str):
        """Learn from comment patterns"""
        comment_lower = comment.lower()
        
        # Learn about content preferences
        if any(word in comment_lower for word in ["outfit", "style", "fashion", "look"]):
            learning = f"Followers are interested in fashion content from {username}"
            self.save_learning(learning, importance=3)
            self.memory.save_hybrid_memory(learning, importance=3, category="instagram_learning")
        
        # Learn about common questions
        if "?" in comment:
            question = comment.split("?")[0] + "?"
            learning = f"Common question on Instagram: {question}"
            self.save_learning(learning, importance=2)
            self.memory.save_hybrid_memory(learning, importance=2, category="instagram_questions")
        
        # Learn about collaboration interest
        if any(word in comment_lower for word in ["collab", "collaboration"]):
            learning = f"@{username} is interested in collaborating!"
            self.save_learning(learning, importance=3)
            self.memory.save_hybrid_memory(learning, importance=3, category="instagram_collabs")
    
    def save_instagram_memory(self, content: str, memory_type: str = "general"):
        """Save Instagram-specific memory"""
        self.file_tool.write_file(
            os.path.join(self.data_dir, f"memory_{memory_type}_{datetime.now().strftime('%Y%m%d')}.txt"),
            f"{datetime.now().isoformat()}: {content}"
        )
        
        # Also save to hybrid memory
        self.memory.save_hybrid_memory(
            f"Instagram {memory_type}: {content[:100]}",
            importance=2,
            category=f"instagram_{memory_type}"
        )
    
    def export_instagram_data(self) -> str:
        """Export all Instagram data to a single file"""
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
        """Sync all Instagram data to local memory and files"""
        self.last_sync = datetime.now()
        
        # Update stats
        self.get_profile_data()
        
        # Learn from Instagram
        insights = self.learn_from_instagram()
        
        # Save sync info
        sync_fact = f"Instagram sync at {self.last_sync.strftime('%H:%M')} - {self.stats['followers']} followers"
        self.memory.save_hybrid_memory(sync_fact, importance=1, category="instagram_sync")
        self.save_learning(sync_fact, importance=1)
        
        # Export data
        self.export_instagram_data()
        
        # Save all data
        self._save_data()
        
        print(f"📸 Instagram synced! Followers: {self.stats['followers']}")
        return self.stats
