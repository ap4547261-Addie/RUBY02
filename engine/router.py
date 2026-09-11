import os
import json
import threading
import random
from datetime import datetime, timedelta

try:
    import config
except ImportError:
    config = None

try:
    from personality.ruby import RUBY_PROMPT
except ImportError:
    RUBY_PROMPT = "You are Ruby, a sassy, emotional human girl."

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


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


class BrainRouter:
    def __init__(self, model_path="tinyllama.gguf", user_id="default_user"):
        self.sleep_scheduler = RubySleepScheduler()
        self.user_id = user_id
        self.model = None

        # Resolve model path safely across application paths and local fallbacks
        resolved_model_path = model_path
        if not os.path.exists(resolved_model_path):
            local_candidates = [
                model_path,
                "tinyllama.gguf",
                "assets/tinyllama.gguf",
                os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "tinyllama.gguf")
            ]
            for candidate in local_candidates:
                if candidate and os.path.exists(candidate):
                    resolved_model_path = candidate
                    break

        if Llama is not None and os.path.exists(resolved_model_path):
            try:
                print(f"🧠 Loading native model from {resolved_model_path}...")
                self.model = Llama(
                    model_path=resolved_model_path,
                    n_ctx=512,          # Optimized context window to prevent CPU choking on mobile
                    n_threads=4,        # Restrict CPU threads to avoid maxing out mobile cores
                    n_batch=128,        # Smaller batch size for faster token processing
                    verbose=True
                )
                print("✨ Native model loaded successfully!")
            except Exception as e:
                import traceback
                print(f"❌ Failed to load native model weights: {e}")
                traceback.print_exc()
        else:
            print(f"⚠️ Warning: llama_cpp package not found or model file not found at: {os.path.abspath(resolved_model_path)}")

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

    def _generate_fallback(self, user_msg: str) -> str:
        msg_lower = user_msg.lower().strip()
        if any(g in msg_lower for g in ["hi", "hyy", "hello", "hey", "sup"]):
            return "Hey... took you long enough to say something."
        elif "who are you" in msg_lower or "your name" in msg_lower:
            return "I'm Ruby. Your favorite psychologist-in-training, whether you admit it or not."
        return f"I heard '{user_msg}', but my mind's wandering somewhere else right now, Addie..."

    def route_request(self, messages, personality=None, user_id=None):
        uid = user_id if user_id else self.user_id

        # Handle midnight sleep check
        if self.sleep_scheduler.should_sleep_now():
            self.sleep_scheduler.start_daily_sleep()
        if self.sleep_scheduler.is_sleeping:
            if not self.sleep_scheduler.check_wake_up():
                status = self.sleep_scheduler.get_status()
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

        # 2. Native generation via embedded llama-cpp-python
        if self.model and last_user_msg:
            try:
                sys_prompt = personality or RUBY_PROMPT
                prompt = f"{sys_prompt}\n\nUser: {last_user_msg}\nRuby:"
                
                output = self.model(
                    prompt,
                    max_tokens=150,
                    stop=["User:", "\nUser:"],
                    temperature=0.7,
                    echo=False
                )
                response_text = output["choices"][0]["text"].strip()
                if response_text:
                    return {"source": "native_local", "response": response_text}
            except Exception as e:
                print(f"Native inference error: {e}")

        # 3. Fallback if native model isn't loaded or fails
        fallback_text = self._generate_fallback(last_user_msg or "")
        return {"source": "fallback", "response": fallback_text}

    def get_energy_status(self):
        return self.sleep_scheduler.get_status()
