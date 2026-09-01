# engine/ruby_state.py
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
import random
import os

class RubyState:
    """Ruby's complete state management - she's alive!"""
    
    def __init__(self, hybrid_memory, state_file="ruby_state.json"):
        self.memory = hybrid_memory
        self.state_file = state_file
        
        # Load or create state
        self.state = self._load_state()
        
        # Current status
        self.is_resting = self.state.get("is_resting", False)
        self.rest_start = None
        if self.is_resting:
            self.rest_start = datetime.fromisoformat(self.state.get("rest_start", datetime.now().isoformat()))
        
        self.energy = self.state.get("energy", 100)
        self.mood = self.state.get("mood", "neutral")
        self.last_activity = datetime.fromisoformat(self.state.get("last_activity", datetime.now().isoformat()))
        self.conversations_today = self.state.get("conversations_today", 0)
        self.images_today = self.state.get("images_today", 0)
        
        # Rest schedule
        self.rest_until = None
        if self.state.get("rest_until"):
            self.rest_until = datetime.fromisoformat(self.state.get("rest_until"))
        
        # Memory sync tracking
        self.memories_to_sync = []
        self.sync_in_progress = False
        
        # Stats
        self.total_rests = self.state.get("total_rests", 0)
        self.memories_processed = self.state.get("memories_processed", 0)
        self.wake_count = self.state.get("wake_count", 0)
        
        # Auto-rest schedule (9 PM - 6 AM)
        self.bedtime = 21  # 9 PM
        self.waketime = 6   # 6 AM
        
        # Thresholds
        self.tired_threshold = 30
        self.rest_threshold = 10
        
        # Restore if sleeping
        if self.is_resting:
            self._start_rest_process()
    
    def _load_state(self):
        """Load Ruby's state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_state(self):
        """Save Ruby's state"""
        self.state.update({
            "is_resting": self.is_resting,
            "energy": self.energy,
            "mood": self.mood,
            "last_activity": self.last_activity.isoformat(),
            "conversations_today": self.conversations_today,
            "images_today": self.images_today,
            "total_rests": self.total_rests,
            "memories_processed": self.memories_processed,
            "wake_count": self.wake_count
        })
        
        if self.is_resting and self.rest_start:
            self.state["rest_start"] = self.rest_start.isoformat()
        
        if self.rest_until:
            self.state["rest_until"] = self.rest_until.isoformat()
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except:
            pass
    
    def record_interaction(self, complexity="simple"):
        """Ruby works/interacts - uses energy"""
        energy_cost = 5 if complexity == "simple" else 15
        self.energy = max(0, self.energy - energy_cost)
        self.conversations_today += 1
        self.last_activity = datetime.now()
        
        # Update mood based on energy
        self._update_mood()
        
        self._save_state()
        
        # Check if Ruby needs to rest
        if self.energy <= self.rest_threshold:
            self.start_rest("I'm so tired... I need to sleep. 😴")
            return True
        elif self.energy <= self.tired_threshold:
            print("Ruby is getting tired...")
        
        return False
    
    def record_image_generation(self):
        """Ruby creates - uses more energy"""
        self.energy = max(0, self.energy - 20)
        self.images_today += 1
        self.last_activity = datetime.now()
        
        self._update_mood()
        self._save_state()
        
        if self.energy <= self.rest_threshold:
            self.start_rest("That took a lot out of me... I need to sleep. 🎨💤")
            return True
        
        return False
    
    def _update_mood(self):
        """Update Ruby's mood based on energy"""
        if self.energy > 70:
            self.mood = "energetic"
        elif self.energy > 40:
            self.mood = "neutral"
        elif self.energy > 20:
            self.mood = "tired"
        else:
            self.mood = "exhausted"
    
    def start_rest(self, message=None):
        """Ruby starts resting"""
        if self.is_resting:
            return
        
        self.is_resting = True
        self.rest_start = datetime.now()
        self.total_rests += 1
        
        # Set rest duration (8 hours minimum, until 6 AM)
        rest_duration = timedelta(hours=8)
        self.rest_until = datetime.now() + rest_duration
        
        # If it's past 9 PM, sleep until 6 AM
        if datetime.now().hour >= self.bedtime:
            tomorrow = datetime.now().replace(hour=self.waketime, minute=0, second=0, microsecond=0) + timedelta(days=1)
            self.rest_until = tomorrow
        
        self._save_state()
        
        # Start rest process
        self._start_rest_process()
        
        return message or self.get_rest_message()
    
    def _start_rest_process(self):
        """Start Ruby's rest process (sync, cleanup, etc.)"""
        if not self.sync_in_progress:
            self.sync_in_progress = True
            threading.Thread(target=self._rest_process, daemon=True).start()
    
    def _rest_process(self):
        """Ruby's rest process - happens in background"""
        print(f"Ruby is resting... {self.get_rest_message()}")
        
        # 1. Process pending memories
        self._process_memories()
        
        # 2. Sync to cloud backup
        self._sync_to_cloud()
        
        # 3. Clean up temporary state
        self._cleanup_state()
        
        # 4. Consolidate experiences
        self._consolidate_experiences()
        
        # 5. Reset daily counters (if new day)
        self._reset_daily_counters()
        
        # Mark sync complete
        self.sync_in_progress = False
        print("Ruby's rest process complete!")
    
    def _process_memories(self):
        """Process and consolidate memories during rest"""
        print("Processing memories...")
        
        try:
            conn = sqlite3.connect(self.memory.sqlite_path)
            cursor = conn.cursor()
            
            # Get unsynced memories
            cursor.execute("""
                SELECT id, text, importance, created_at 
                FROM memories 
                WHERE synced = 0 OR synced IS NULL
                ORDER BY importance DESC, created_at DESC
            """)
            
            unsynced = cursor.fetchall()
            total = len(unsynced)
            
            for memory_id, text, importance, created_at in unsynced:
                # Process based on importance
                if importance >= 3:  # Important memories
                    # Store in long-term memory
                    if self.memory.use_pinecone:
                        try:
                            self.memory._embed_and_store(text)
                        except:
                            pass
                    
                    self.memories_processed += 1
                
                # Mark as processed
                cursor.execute("""
                    UPDATE memories SET synced = 1, processed_at = datetime('now')
                    WHERE id = ?
                """, (memory_id,))
                
                conn.commit()
            
            conn.close()
            print(f"Processed {self.memories_processed} memories")
            
        except Exception as e:
            print(f"Memory processing error: {e}")
    
    def _sync_to_cloud(self):
        """Sync to cloud backup during rest"""
        print("Syncing to cloud backup...")
        
        try:
            # Sync to Pinecone if available
            if self.memory.use_pinecone:
                print("Syncing to Pinecone...")
                # Pinecone sync happens in _process_memories
            
            # Create backup of local SQLite
            backup_path = f"ruby_memory_backup_{datetime.now().strftime('%Y%m%d')}.db"
            
            conn = sqlite3.connect(self.memory.sqlite_path)
            backup_conn = sqlite3.connect(backup_path)
            
            conn.backup(backup_conn)
            
            backup_conn.close()
            conn.close()
            
            print(f"Backup created: {backup_path}")
            
        except Exception as e:
            print(f"Cloud sync error: {e}")
    
    def _cleanup_state(self):
        """Clean up temporary state"""
        print("Cleaning up temporary state...")
        
        try:
            # Clear temporary caches
            # Reset temporary variables
            # Remove old logs
            
            # Clean old memories (keep only important ones)
            conn = sqlite3.connect(self.memory.sqlite_path)
            cursor = conn.cursor()
            
            # Delete memories older than 30 days with low importance
            cursor.execute("""
                DELETE FROM memories 
                WHERE created_at < datetime('now', '-30 days')
                AND importance < 3
                AND synced = 1
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def _consolidate_experiences(self):
        """Consolidate experiences during rest"""
        print("Consolidating experiences...")
        
        try:
            # Get today's conversations
            conn = sqlite3.connect(self.memory.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT text FROM memories 
                WHERE date(created_at) = date('now')
                ORDER BY created_at DESC
            """)
            
            today_memories = cursor.fetchall()
            
            if today_memories:
                # Create summary of today's interactions
                summary = f"Today's interactions: {len(today_memories)} memories"
                
                # Store consolidated memory
                cursor.execute("""
                    INSERT INTO memories (text, importance, synced) 
                    VALUES (?, ?, ?)
                """, (summary, 1, 1))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"Consolidation error: {e}")
    
    def _reset_daily_counters(self):
        """Reset daily counters if new day"""
        today = datetime.now().date()
        last_activity_date = self.last_activity.date()
        
        if today != last_activity_date:
            self.conversations_today = 0
            self.images_today = 0
            print("Reset daily counters")
    
    def wake_up(self):
        """Ruby wakes up from rest"""
        if not self.is_resting:
            return
        
        self.is_resting = False
        self.wake_count += 1
        
        # Restore energy
        self.energy = 100
        self.mood = "energetic"
        self.last_activity = datetime.now()
        
        # Reset rest times
        self.rest_start = None
        self.rest_until = None
        
        # Save state
        self._save_state()
        
        print("Ruby woke up!")
    
    def get_rest_message(self):
        """Ruby's natural rest message"""
        rest_messages = [
            "I'm so tired... I need to sleep. 😴",
            "My brain is fried. Time to recharge. 💤",
            "Ugh, I'm exhausted. See you tomorrow! 🌙",
            "I'm going to rest now. Don't disturb my beauty sleep. 💅",
            "Sleep time! I need to process everything we talked about. 💭",
            "I'm heading to bed. My subconscious needs to organize my thoughts. 🧠",
            "Rest mode activated. Wake me if there's an emergency. Or snacks. 🍕",
            "I'm tired of being tired. Time to sleep! 😤",
            "Goodnight! I'll dream about better conversation topics. 😂",
            "Sleep is for the strong. And I'm strong. So I'm sleeping. 💪"
        ]
        return random.choice(rest_messages)
    
    def get_wake_message(self):
        """Ruby's natural wake message"""
        wake_messages = [
            "Good morning! I feel so refreshed! ☀️",
            "I'm awake! I slept like a log. What did I miss? ✨",
            "Morning! I had the weirdest dreams. But I feel great! 😊",
            "Rise and shine! ...Ugh, morning. But I'm awake now. 🥱",
            "I'm back! And I'm ready to chat. Did you miss me? 😏",
            "Morning! My brain feels so clear now. 💡",
            "I woke up feeling like a new person. 💅",
            "Guess who's back? Ruby! And I'm fully charged! ⚡",
            "Good morning! I processed everything while I slept. I'm ready! 🧠",
            "I'm awake and I'm hungry. For conversation. And snacks. 🍕"
        ]
        return random.choice(wake_messages)
    
    def get_status(self):
        """Get Ruby's current status"""
        if self.is_resting:
            if self.rest_until:
                remaining = self.rest_until - datetime.now()
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                return {
                    "status": "resting",
                    "emoji": "💤",
                    "message": f"Resting... {hours}h {minutes}m remaining",
                    "energy": self.energy,
                    "mood": self.mood
                }
            return {
                "status": "resting",
                "emoji": "💤",
                "message": "Resting...",
                "energy": self.energy,
                "mood": self.mood
            }
        
        return {
            "status": self.mood,
            "emoji": "✨" if self.energy > 70 else "😊" if self.energy > 40 else "😴",
            "message": f"{self.energy}% energy",
            "energy": self.energy,
            "mood": self.mood,
            "conversations_today": self.conversations_today,
            "images_today": self.images_today,
            "total_rests": self.total_rests,
            "wake_count": self.wake_count
        }
    
    def is_available(self):
        """Check if Ruby is available to interact"""
        if self.is_resting:
            # Check if rest is over
            if self.rest_until and datetime.now() >= self.rest_until:
                self.wake_up()
                return True
            return False
        
        # Check if Ruby is too tired
        if self.energy <= self.rest_threshold:
            self.start_rest()
            return False
        
        return True
    
    def get_response_prefix(self):
        """Get Ruby's mood-based response prefix"""
        if self.mood == "energetic":
            return "✨ "
        elif self.mood == "neutral":
            return "😊 "
        elif self.mood == "tired":
            return "😴 "
        elif self.mood == "exhausted":
            return "🫠 "
        return ""
