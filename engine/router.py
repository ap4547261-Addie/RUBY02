# =====================================================================
# engine/router.py – Ruby's Brain Router, Energy Manager & Sleep Scheduler
# =====================================================================

import os
import json
import time
import threading
import subprocess
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
    - Backup and state maintenance
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

        print("✨ All offline sync operations completed!")

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
    def __init__(self, local_model="tinyllama", user_id="default_user"):
        self.energy = EnergyManager()
        self.sleep_scheduler = self.energy._sleep_scheduler
        self.local_model = local_model
        self.profile = ConversationProfile()
        self.user_id = user_id
        print("🧠 100% Offline BrainRouter initialized!")

    def _call_local_brain(self, messages):
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
        
        if isinstance(memories, str):
            memories_list = [memories]
        else:
            memories_list = memories or []

        for mem in memories_list:
            if isinstance(mem, str) and "Q: " in mem and "\nA: " in mem:
                parts = mem.split("\nA: ")
                if len(parts) > 1:
                    return parts[1].strip()

        return None

    def route_request(self, messages, personality=None, user_id=None):
        uid = user_id if user_id else self.user_id

        if not self.energy.is_available():
            status = self.energy.get_energy_status()
            return {"source": "sleeping", "response": status["message"]}

        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        # 1. Check local vector memory database first
        local_answer = self._call_local_brain(messages)
        if local_answer is not None:
            return {"source": "local_brain", "response": local_answer}

        # 2. Fall back to local Ollama inference model for conversational responses / greetings
        if last_user_msg:
            try:
                sys_prompt = personality or "You are Ruby, a sassy, emotional girl with orange hair."
                prompt = f"{sys_prompt}\n\nUser: {last_user_msg}\nRuby:"
                
                cmd = ["ollama", "run", self.local_model, prompt]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                response = result.stdout.strip()
                if response:
                    return {"source": "local_ollama", "response": response}
            except Exception as e:
                print(f"Local Ollama generation error: {e}")

        # 3. Final fallback if local execution fails entirely
        return {"source": "fallback", "response": "Hyy? Is that all you've got to say? Spit it out."}

    def get_energy_status(self):
        return self.energy.get_energy_status()
