# engine/router.py - HARDCODED KEY TEST (remove after verification)
import os
import json
import time
import socket
import threading
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import random
from tools.profile import ConversationProfile

try:
    import config
except ImportError:
    config = None

class RubyEnergySystem:
    def __init__(self):
        self.chat_keys = []
        self.image_keys = []

        def get_key(name):
            key = os.getenv(name)
            if key:
                return key
            if config is not None:
                return getattr(config, name, None)
            return None

        for i in range(1, 5):
            key = get_key(f"GEMINI_API_KEY{i}")
            if key:
                self.chat_keys.append(key)

        for i in range(5, 10):
            key = get_key(f"GEMINI_API_KEY{i}")
            if key:
                self.image_keys.append(key)

        if not self.chat_keys and not self.image_keys:
            fallback = get_key("GEMINI_API_KEY")
            if fallback:
                self.chat_keys = [fallback]
                self.image_keys = [fallback]

        print(f"🔑 Loaded {len(self.chat_keys)} chat keys and {len(self.image_keys)} image keys.")

        self.chat_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.chat_keys}
        self.image_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.image_keys}
        self.chat_index = 0
        self.image_index = 0
        self.lock = threading.Lock()
        self.is_sleeping = False
        self.sleep_until = None
        self.total_sleeps = 0
        self.current_wake_start = datetime.now()
        self.longest_wake = 0
        self.energy = 100
        self.conversations_today = 0
        self.images_today = 0
        self.tired_threshold = 30
        self.sleep_threshold = 10

    def get_chat_key(self):
        with self.lock:
            if self.is_sleeping:
                if self.sleep_until and datetime.now() < self.sleep_until:
                    return None
                else:
                    self._wake_up()

            today = datetime.now().date()
            for key in self.chat_usage:
                if self.chat_usage[key]["day"] != today:
                    self.chat_usage[key]["count"] = 0
                    self.chat_usage[key]["day"] = today

            for _ in range(len(self.chat_keys)):
                key = self.chat_keys[self.chat_index]
                if self.chat_usage[key]["count"] < 20:
                    self.chat_usage[key]["count"] += 1
                    self.chat_index = (self.chat_index + 1) % len(self.chat_keys)
                    print(f"Using chat key {key[:10]}... (count: {self.chat_usage[key]['count']}/20)")
                    return key
                self.chat_index = (self.chat_index + 1) % len(self.chat_keys)

            self._go_to_sleep()
            return None

    def get_image_key(self):
        with self.lock:
            if self.is_sleeping:
                if self.sleep_until and datetime.now() < self.sleep_until:
                    return None
                else:
                    self._wake_up()

            today = datetime.now().date()
            for key in self.image_usage:
                if self.image_usage[key]["day"] != today:
                    self.image_usage[key]["count"] = 0
                    self.image_usage[key]["day"] = today

            for _ in range(len(self.image_keys)):
                key = self.image_keys[self.image_index]
                if self.image_usage[key]["count"] < 20:
                    self.image_usage[key]["count"] += 1
                    self.image_index = (self.image_index + 1) % len(self.image_keys)
                    print(f"Using image key {key[:10]}... (count: {self.image_usage[key]['count']}/20)")
                    return key
                self.image_index = (self.image_index + 1) % len(self.image_keys)

            self._go_to_sleep()
            return None

    def _sync_and_reset(self):
        try:
            from main import conversation_history, save_chat_history
            print("💾 Ruby is syncing data during sleep...")
            conversation_history.clear()
            save_chat_history()
            print("🗑️ Chat history reset for new day!")
            self.conversations_today = 0
            self.images_today = 0
            print("📊 Daily counters reset!")
        except Exception as e:
            print(f"❌ Sync error: {e}")

    def _go_to_sleep(self):
        if self.is_sleeping:
            return

        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        total_used = chat_used + image_used
        total_limit = (len(self.chat_keys) + len(self.image_keys)) * 20

        if total_used == 0:
            print("💪 Ruby has full energy! No sleep needed!")
            return

        ratio = total_used / total_limit if total_limit > 0 else 0
        if ratio >= 0.9:
            sleep_hours = 8
        elif ratio >= 0.6:
            sleep_hours = 6
        elif ratio >= 0.4:
            sleep_hours = 4
        elif ratio >= 0.1:
            sleep_hours = 2
        else:
            sleep_hours = 0

        if sleep_hours == 0:
            print("💪 Ruby doesn't need sleep right now!")
            return

        self.is_sleeping = True
        self.total_sleeps += 1
        self.sleep_until = datetime.now() + timedelta(hours=sleep_hours)

        self._sync_and_reset()
        # No memory compression
        try:
            from main import gmail, cloud, MEMORY_DB, KNOWLEDGE_DB
            if gmail:
                gmail.backup_db(MEMORY_DB, "ruby_memory.db")
                gmail.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
            if cloud:
                cloud.backup_db(MEMORY_DB, "ruby_memory.db")
                cloud.backup_db(KNOWLEDGE_DB, "ruby_knowledge.db")
            print("✅ Backups completed.")
        except Exception as e:
            print(f"⚠️ Backup on sleep failed: {e}")

        awake_duration = (datetime.now() - self.current_wake_start).seconds / 3600
        if awake_duration > self.longest_wake:
            self.longest_wake = awake_duration

        print(f"😴 Ruby is going to sleep for {sleep_hours} hours")
        print(f"🕐 Will wake at {self.sleep_until.strftime('%I:%M %p')}")
        print(f"📊 Keys exhausted: {total_used}/{total_limit}")

    def _wake_up(self):
        self.is_sleeping = False
        self.sleep_until = None
        self.current_wake_start = datetime.now()
        self.energy = 100

        today = datetime.now().date()
        for key in self.chat_usage:
            self.chat_usage[key]["count"] = 0
            self.chat_usage[key]["day"] = today
        for key in self.image_usage:
            self.image_usage[key]["count"] = 0
            self.image_usage[key]["day"] = today

        print("✨ Ruby woke up refreshed!")

    def get_energy_status(self):
        if self.is_sleeping:
            if self.sleep_until:
                remaining = self.sleep_until - datetime.now()
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                return {
                    "status": "sleeping",
                    "emoji": "💤",
                    "message": f"Sleeping... {hours}h {minutes}m remaining",
                    "energy": self.energy,
                    "wakes_at": self.sleep_until
                }
            return {
                "status": "sleeping",
                "emoji": "💤",
                "message": "Sleeping...",
                "energy": self.energy
            }

        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        total_used = chat_used + image_used
        total_limit = (len(self.chat_keys) + len(self.image_keys)) * 20
        energy_percent = max(0, 100 - (total_used / total_limit * 100))

        if energy_percent > 70:
            status = "energetic"
            emoji = "✨"
            message = "Full energy! Ready to chat!"
        elif energy_percent > 40:
            status = "normal"
            emoji = "😊"
            message = "Feeling good!"
        elif energy_percent > 20:
            status = "tired"
            emoji = "😴"
            message = "Getting tired..."
        else:
            status = "very_tired"
            emoji = "🫠"
            message = "Very tired... need rest soon"

        return {
            "status": status,
            "emoji": emoji,
            "message": message,
            "energy": energy_percent,
            "chat_used": chat_used,
            "image_used": image_used,
            "total_used": total_used,
            "total_limit": total_limit,
            "remaining": total_limit - total_used
        }

    def is_available(self):
        if self.is_sleeping:
            if self.sleep_until and datetime.now() >= self.sleep_until:
                self._wake_up()
                return True
            return False

        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        total_used = chat_used + image_used
        total_limit = (len(self.chat_keys) + len(self.image_keys)) * 20

        if total_used >= total_limit:
            self._go_to_sleep()
            return False

        return True

    def get_sleep_message(self):
        return "💤"

    def get_wake_message(self):
        return "✨"


class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None, user_id="default_user"):
        self.energy = RubyEnergySystem()
        self.local_model_path = local_model_path

        # ======================================================
        # HARDCODED KEY – replace YOUR_ACTUAL_KEY with your key
        # ======================================================
        self.cloud_api_key = "AQ.Ab8RN6K4tQSW9wMk3P3SO29lSGuZg8CvZy_Km7mj5xea60i6mQ"   # <--- PASTE YOUR KEY HERE

        # If you want to fall back to config/env, comment the line above
        # and uncomment the lines below:
        # self.cloud_api_key = cloud_api_key or os.getenv("GEMINI_API_KEY")
        # if not self.cloud_api_key and self.energy.chat_keys:
        #     self.cloud_api_key = self.energy.chat_keys[0]

        self.cloud_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
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

        if "?" in last_user_msg:
            hybrid_memory.save_hybrid_memory(
                f"User asked: {last_user_msg}",
                importance=3,
                category="user_questions"
            )
        else:
            hybrid_memory.save_hybrid_memory(
                f"User said: {last_user_msg}",
                importance=2,
                category="user_messages"
            )

        memories = hybrid_memory.search_memories(last_user_msg)
        for mem in memories:
            if mem.startswith("Q: ") and "\nA: " in mem:
                answer = mem.split("\nA: ", 1)[1]
                return answer

        return None

    def _call_cloud(self, messages, personality=None):
        if not self.cloud_api_key:
            return None

        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        url = f"{self.cloud_url}?key={self.cloud_api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        if personality:
            data["systemInstruction"] = {"parts": [{"text": personality}]}

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                if "candidates" in response_data and response_data["candidates"]:
                    return response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return None
        except Exception as e:
            print(f"Cloud call error: {e}")
            raise

    def _get_style_instruction(self, user_id):
        stats = self.profile.get_stats(user_id)
        if stats and stats['total_turns'] > 3:
            return self.profile.build_style_instruction(stats)
        return ""

    def route_request(self, messages, personality=None, use_cloud_preferred=True, user_id=None):
        uid = user_id if user_id else self.user_id

        if not self.energy.is_available():
            if self.energy.is_sleeping:
                if self.energy.sleep_until and datetime.now() < self.energy.sleep_until:
                    return {"source": "sleeping", "response": "💤"}
                else:
                    self.energy._wake_up()
                    return {"source": "waking_up", "response": "✨"}
            self.energy._go_to_sleep()
            return {"source": "going_to_sleep", "response": "💤"}

        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        local_answer = self._call_local_brain(messages)
        if local_answer is not None:
            if last_user_msg:
                self.profile.update(uid, last_user_msg, local_answer)
            try:
                from main import hybrid_memory
                hybrid_memory.save_hybrid_memory(
                    f"Ruby replied (local): {local_answer}",
                    importance=2,
                    category="ruby_responses"
                )
            except:
                pass
            return {"source": "local_brain", "response": local_answer}

        if use_cloud_preferred:
            chat_key = self.energy.get_chat_key()
            if chat_key is not None:
                # Use the hardcoded key if available, otherwise fallback to chat_key
                if self.cloud_api_key:
                    # Already set; no need to override
                    pass
                else:
                    self.cloud_api_key = chat_key

                style_instr = self._get_style_instruction(uid)
                if style_instr:
                    if personality is None:
                        personality = ""
                    personality += "\n\n" + style_instr

                max_retries = 3
                backoff_delay = 3
                for attempt in range(max_retries):
                    try:
                        print("========== GEMINI REQUEST ==========")
                        print(f"Attempt: {attempt + 1}")
                        response = self._call_cloud(messages, personality)
                        if response:
                            print("========== GEMINI SUCCESS ==========")
                            self.energy.conversations_today += 1
                            if last_user_msg:
                                self.profile.update(uid, last_user_msg, response)
                            try:
                                from main import hybrid_memory
                                if last_user_msg:
                                    hybrid_memory.save_hybrid_memory(
                                        f"Q: {last_user_msg}\nA: {response}",
                                        importance=3,
                                        category="qa_pair"
                                    )
                                    hybrid_memory.save_hybrid_memory(
                                        f"User asked: {last_user_msg}",
                                        importance=3,
                                        category="user_questions"
                                    )
                                hybrid_memory.save_hybrid_memory(
                                    f"Ruby replied: {response}",
                                    importance=2,
                                    category="ruby_responses"
                                )
                            except:
                                pass
                            if self.energy.get_energy_status()["energy"] < 20:
                                response += "\n\nUgh, that took a lot out of me... I'm getting tired."
                            return {"source": "cloud", "response": response}
                    except urllib.error.HTTPError as e:
                        status_code = e.code
                        try:
                            error_message = e.read().decode("utf-8")
                        except:
                            error_message = str(e)
                        print(f"HTTP Error {status_code}: {error_message}")
                        if status_code == 429:
                            with self.energy.lock:
                                if chat_key in self.energy.chat_usage:
                                    self.energy.chat_usage[chat_key]["count"] = 20
                            continue
                        if status_code == 503:
                            if attempt < max_retries - 1:
                                print(f"Retrying in {backoff_delay}s...")
                                time.sleep(backoff_delay)
                                backoff_delay *= 2
                                continue
                        break
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        break

        try:
            from main import hybrid_memory
            questions = hybrid_memory.get_memories_by_category("user_questions")
            if questions:
                question = random.choice(questions)
                if question.startswith("User asked: "):
                    question = question[len("User asked: "):]
                if last_user_msg:
                    self.profile.update(uid, last_user_msg, question)
                return {"source": "fallback", "response": question}
        except:
            pass

        return {"source": "fallback", "response": "I'm not sure how to answer that."}
