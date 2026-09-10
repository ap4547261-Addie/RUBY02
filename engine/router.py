# =====================================================================
# engine/router.py – Ruby's Brain Router, Energy Manager & Sleep Scheduler
# =====================================================================

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
        self.sleep_duration_minutes = 30

        print("🌙 Ruby's Daily Sleep Scheduler initialized")

    def _is_within_sleep_window(self):
        now = datetime.now()
        start = now.replace(hour=self.sleep_start_hour, minute=self.sleep_start_minute, second=0, microsecond=0)
        end = start + timedelta(minutes=self.sleep_duration_minutes)
        return start <= now < end

    def should_sleep_now(self):
        with self.lock:
            today = datetime.now().date()
            if self.last_sleep_date == today:
                return False
            if self.is_sleeping:
                return True
            return self._is_within_sleep_window()

    def start_daily_sleep(self):
        with self.lock:
            if self.is_sleeping:
                return

            self.is_sleeping = True
            sleep_minutes = self.sleep_duration_minutes
            self.sleep_until = datetime.now() + timedelta(minutes=sleep_minutes)
            self.last_sleep_date = datetime.now().date()

            print(f"😴 Ruby is going to sleep for {sleep_minutes} minutes (midnight sync)")
            sync_thread = threading.Thread(target=self._perform_sync)
            sync_thread.daemon = True
            sync_thread.start()

    def _perform_sync(self):
        try:
            from main import save_chat_history
            save_chat_history()
        except Exception:
            pass

        try:
            from main import hybrid_memory
            hybrid_memory.compress_memories(days_threshold=30)
        except Exception:
            pass

        try:
            from main import gmail, cloud, MEMORY_DB, KNOWLEDGE_DB
            if gmail:
                gmail.backup_db(MEMORY_DB, "ruby_memory.db")
                gmail.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
            if cloud:
                cloud.backup_db(MEMORY_DB, "ruby_memory.db")
                cloud.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
        except Exception:
            pass

        print("✨ All sync operations completed!")

    def check_wake_up(self):
        with self.lock:
            if not self.is_sleeping:
                return False
            if self.sleep_until and datetime.now() >= self.sleep_until:
                self._wake_up()
                return True
            return False

    def _wake_up(self):
        self.is_sleeping = False
        self.sleep_until = None
        print("✨ Ruby woke up refreshed after midnight sync!")

    def get_status(self):
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


class EnergyManager:
    """Manages Ruby's energy and sleep integration for UI compatibility"""
    def __init__(self):
        self._energy_val = 100
        self.is_sleeping = False
        self.sleep_until = None
        self._sleep_scheduler = RubySleepScheduler()

    def __int__(self):
        return self._energy_val

    def __index__(self):
        return self._energy_val

    def __eq__(self, other):
        return self._energy_val == other

    def __gt__(self, other):
        return self._energy_val > other

    def __lt__(self, other):
        return self._energy_val < other

    def __ge__(self, other):
        return self._energy_val >= other

    def __le__(self, other):
        return self._energy_val <= other

    def __str__(self):
        return str(self._energy_val)

    def __repr__(self):
        return str(self._energy_val)

    def is_available(self):
        if self._sleep_scheduler.should_sleep_now():
            self._go_to_sleep()
        if self.is_sleeping:
            if self._sleep_scheduler.check_wake_up():
                self._wake_up()
        return not self.is_sleeping

    def _go_to_sleep(self):
        self.is_sleeping = True
        self._sleep_scheduler.start_daily_sleep()
        self.sleep_until = self._sleep_scheduler.sleep_until

    def _wake_up(self):
        self.is_sleeping = False
        self.sleep_until = None
        self._sleep_scheduler._wake_up()

    def get_energy_status(self):
        status = self._sleep_scheduler.get_status()
        status["energy"] = self._energy_val
        return status


class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None, user_id="default_user", brain_core=None):
        self.energy = EnergyManager()
        self.sleep_scheduler = self.energy._sleep_scheduler
        self.local_model_path = local_model_path
        self.profile = ConversationProfile()
        self.user_id = user_id
        self.brain_core = brain_core

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

        memories = hybrid_memory.search_memories(last_user_msg)
        for mem in memories:
            if mem.startswith("Q: ") and "\nA: " in mem:
                answer = mem.split("\nA: ", 1)[1]
                return answer

        return None

    def route_request(self, messages, personality=None, use_cloud_preferred=False, user_id=None):
        uid = user_id if user_id else self.user_id

        if not self.energy.is_available():
            status = self.energy.get_energy_status()
            return {"source": "sleeping", "response": status["message"]}

        local_answer = self._call_local_brain(messages)
        if local_answer is not None:
            return {"source": "local_brain", "response": local_answer}

        if self.brain_core:
            last_user_msg = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                    break
            if last_user_msg:
                try:
                    sys_prompt = personality or "You are Ruby, a sassy, emotional girl with orange hair."
                    response = self.brain_core.generate_response(last_user_msg, system_prompt=sys_prompt)
                    if response:
                        return {"source": "local_llm", "response": response}
                except Exception as e:
                    print(f"LLM generation error: {e}")

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

        return {"source": "fallback", "response": "I don't know yet, but I'm learning. Ask me something else?"}

    def get_energy_status(self):
        return self.energy.get_energy_status()
