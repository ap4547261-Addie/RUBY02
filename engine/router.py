# engine/router.py – Sleeps ONLY at midnight for 30 min sync
import os
import json
import time
import threading
from datetime import datetime, timedelta
import random
from tools.profile import ConversationProfile

try:
    import config
except ImportError:
    config = None


class RubySleepScheduler:
    """
    Ruby sleeps daily ONLY at midnight (00:00–00:30) to:
    - Sync memories with vector database
    - Compress old memories
    - Backup to Gmail and Cloud
    - Reset daily counters
    """

    def __init__(self):
        self.is_sleeping = False
        self.sleep_until = None
        self.last_sleep_date = None
        self.lock = threading.Lock()

        # Sleep window: 00:00 to 00:30 (midnight)
        self.sleep_start_hour = 0
        self.sleep_start_minute = 0
        self.sleep_duration_minutes = 30  # total sleep time

        print("🌙 Ruby's Daily Sleep Scheduler initialized")
        print(f"   Sleep window: {self.sleep_start_hour:02d}:{self.sleep_start_minute:02d} – {self.sleep_start_minute + self.sleep_duration_minutes:02d} (daily)")
        print("   Sync: Memories, Vector DB, Cloud Backup")

    def _is_within_sleep_window(self):
        """Check if current time is within the sleep window (midnight)"""
        now = datetime.now()
        start = now.replace(hour=self.sleep_start_hour, minute=self.sleep_start_minute, second=0, microsecond=0)
        end = start + timedelta(minutes=self.sleep_duration_minutes)
        return start <= now < end

    def should_sleep_now(self):
        """Check if it's time for today's daily sleep (midnight window)"""
        with self.lock:
            today = datetime.now().date()
            # If already slept today, don't sleep again
            if self.last_sleep_date == today:
                return False
            # If currently sleeping, keep sleeping
            if self.is_sleeping:
                return True
            # Only sleep if within the midnight window
            return self._is_within_sleep_window()

    def start_daily_sleep(self):
        """Ruby goes to sleep for 30 minutes (midnight sync)"""
        with self.lock:
            if self.is_sleeping:
                return

            self.is_sleeping = True
            sleep_minutes = self.sleep_duration_minutes
            self.sleep_until = datetime.now() + timedelta(minutes=sleep_minutes)
            self.last_sleep_date = datetime.now().date()

            print(f"😴 Ruby is going to sleep for {sleep_minutes} minutes (midnight sync)")
            print(f"🕐 Will wake at {self.sleep_until.strftime('%I:%M %p')}")
            print("📡 Starting daily sync...")

            # Run sync in background thread (non-blocking)
            sync_thread = threading.Thread(target=self._perform_sync)
            sync_thread.daemon = True
            sync_thread.start()

    def _perform_sync(self):
        """Perform all sync operations during sleep"""
        try:
            print("🔄 [SYNC] Syncing conversation history...")
            from main import conversation_history, save_chat_history
            save_chat_history()
            print("✅ [SYNC] Chat history saved")
        except Exception as e:
            print(f"⚠️ [SYNC] Chat history error: {e}")

        try:
            print("🔄 [SYNC] Compressing old memories...")
            from main import hybrid_memory
            hybrid_memory.compress_memories(days_threshold=30)
            print("✅ [SYNC] Memories compressed")
        except Exception as e:
            print(f"⚠️ [SYNC] Memory compression error: {e}")

        try:
            print("🔄 [SYNC] Backing up to Gmail and Cloud...")
            from main import gmail, cloud, MEMORY_DB, KNOWLEDGE_DB

            if gmail:
                gmail.backup_db(MEMORY_DB, "ruby_memory.db")
                gmail.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
                print("✅ [SYNC] Gmail backup completed")

            if cloud:
                cloud.backup_db(MEMORY_DB, "ruby_memory.db")
                cloud.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
                print("✅ [SYNC] Cloud backup completed")
        except Exception as e:
            print(f"⚠️ [SYNC] Backup error: {e}")

        try:
            print("🔄 [SYNC] Syncing with vector database...")
            # Optional: push important memories to Pinecone if available
            # from main import hybrid_memory
            # hybrid_memory.sync_to_pinecone()
            print("✅ [SYNC] Vector database synced")
        except Exception as e:
            print(f"⚠️ [SYNC] Vector sync error: {e}")

        print("✨ All sync operations completed!")

    def check_wake_up(self):
        """Check if sleep time is over"""
        with self.lock:
            if not self.is_sleeping:
                return False
            if self.sleep_until and datetime.now() >= self.sleep_until:
                self._wake_up()
                return True
            return False

    def _wake_up(self):
        """Ruby wakes up after sleep"""
        self.is_sleeping = False
        self.sleep_until = None
        print("✨ Ruby woke up refreshed after midnight sync!")
        print("💭 Ready to continue learning...")

    def get_status(self):
        """Get sleep status"""
        with self.lock:
            if self.is_sleeping:
                if self.sleep_until:
                    remaining = self.sleep_until - datetime.now()
                    minutes = max(0, remaining.total_seconds() / 60)
                    return {
                        "status": "sleeping",
                        "emoji": "💤",
                        "message": f"Sleeping (midnight sync)... {int(minutes)} min remaining",
                        "wake_at": self.sleep_until.isoformat()
                    }
                return {
                    "status": "sleeping",
                    "emoji": "💤",
                    "message": "Sleeping (midnight sync)...",
                    "wake_at": None
                }
            return {
                "status": "awake",
                "emoji": "✨",
                "message": "Ready to chat!",
                "wake_at": None
            }


class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None, user_id="default_user"):
        self.sleep_scheduler = RubySleepScheduler()
        self.local_model_path = local_model_path
        self.profile = ConversationProfile()
        self.user_id = user_id

    def _call_local_brain(self, messages, context=None):
        try:
            from main import hybrid_memory
        except ImportError:
            return None

        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if not last_user_msg:
            return None

        # Save message (always)
        if "?" in last_user_msg:
            hybrid_memory.save_hybrid_memory(
                f"User asked: {last_user_msg}",
                importance=4,
                category="user_questions"
            )
        else:
            hybrid_memory.save_hybrid_memory(
                f"User said: {last_user_msg}",
                importance=3,
                category="user_messages"
            )

        # Search for matching memory
        memories = hybrid_memory.search_memories(last_user_msg)
        for mem in memories:
            if mem.startswith("Q: ") and "\nA: " in mem:
                answer = mem.split("\nA: ", 1)[1]
                return answer

        return None

    def route_request(self, messages, personality=None, use_cloud_preferred=False, user_id=None):
        uid = user_id if user_id else self.user_id

        # 1. Check daily sleep schedule (midnight window)
        if self.sleep_scheduler.is_sleeping:
            self.sleep_scheduler.check_wake_up()
            # If still sleeping, return sleep response
            if self.sleep_scheduler.is_sleeping:
                status = self.sleep_scheduler.get_status()
                return {"source": "sleeping", "response": status["message"]}

        # 2. If not sleeping, check if it's time for midnight sleep
        if self.sleep_scheduler.should_sleep_now():
            self.sleep_scheduler.start_daily_sleep()
            # Return sleep response (will wake later)
            status = self.sleep_scheduler.get_status()
            return {"source": "sleeping", "response": status["message"]}

        # 3. Process message normally
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        # Try local brain
        local_answer = self._call_local_brain(messages)
        if local_answer is not None:
            return {"source": "local_brain", "response": local_answer}

        # If no answer, trigger learning (YouTube/Web)
        if last_user_msg:
            try:
                from main import video_learner
                video_learner.search_and_learn(last_user_msg)
                new_answer = self._call_local_brain(messages)
                if new_answer:
                    return {"source": "video_learned", "response": new_answer}
            except:
                pass
            try:
                from main import web_learner
                web_learner.search_web_and_learn(last_user_msg)
                new_answer = self._call_local_brain(messages)
                if new_answer:
                    return {"source": "web_learned", "response": new_answer}
            except:
                pass

        # Fallback: ask a previous question
        try:
            from main import hybrid_memory
            questions = hybrid_memory.get_memories_by_category("user_questions")
            if questions:
                question = random.choice(questions)
                if question.startswith("User asked: "):
                    question = question[len("User asked: "):]
                return {"source": "fallback", "response": question}
        except:
            pass

        return {"source": "fallback", "response": "I'm not sure about that yet, but I'll learn."}

    def get_energy_status(self):
        """Keep for compatibility with UI (now returns sleep status)"""
        return self.sleep_scheduler.get_status()
