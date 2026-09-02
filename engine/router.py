# engine/router.py
import os
import json
import time
import socket
import threading
import http.client
import urllib.request
import urllib.error
from datetime import datetime, timedelta  
from collections import deque
import random

class RubyEnergySystem:
    """Ruby's personality-driven energy management with 9 keys"""
    
    def __init__(self):
        # Load all 9 keys from environment
        self.chat_keys = []
        self.image_keys = []
        
        # Keys 1-4 for chat (complex questions)
        for i in range(1, 5):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.chat_keys.append(key)
        
        # Keys 5-9 for image generation
        for i in range(5, 10):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.image_keys.append(key)
        
        # Fallback to single key if no numbered keys found
        if not self.chat_keys and not self.image_keys:
            fallback = os.getenv("GEMINI_API_KEY")
            if fallback:
                self.chat_keys = [fallback]
                self.image_keys = [fallback]
        
        # Track usage per key
        self.chat_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.chat_keys}
        self.image_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.image_keys}
        
        self.chat_index = 0
        self.image_index = 0
        self.lock = threading.Lock()
        
        # Sleep state
        self.is_sleeping = False
        self.sleep_until = None
        self.total_sleeps = 0
        self.current_wake_start = datetime.now()
        self.longest_wake = 0
        
        # Energy tracking
        self.energy = 100
        self.conversations_today = 0
        self.images_today = 0
        
        # Thresholds
        self.tired_threshold = 30
        self.sleep_threshold = 10
        
        print(f"RubyEnergySystem initialized with {len(self.chat_keys)} chat keys and {len(self.image_keys)} image keys")
    
    def get_chat_key(self):
        """Get available chat key with automatic rotation"""
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
        """Get available image key with automatic rotation"""
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
        """Sync data and reset chat history for new day"""
        try:
            from main import conversation_history, save_chat_history
            
            print("💾 Ruby is syncing data during sleep...")
            
            # Reset chat history
            conversation_history.clear()
            save_chat_history()
            
            print("🗑️ Chat history reset for new day!")
            
            # Reset daily counters
            self.conversations_today = 0
            self.images_today = 0
            
            print("📊 Daily counters reset!")
            
        except Exception as e:
            print(f"❌ Sync error: {e}")
    
    def _go_to_sleep(self):
        """Ruby goes to sleep - duration based on how many keys are exhausted"""
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
        
        awake_duration = (datetime.now() - self.current_wake_start).seconds / 3600
        if awake_duration > self.longest_wake:
            self.longest_wake = awake_duration
        
        print(f"😴 Ruby is going to sleep for {sleep_hours} hours")
        print(f"🕐 Will wake at {self.sleep_until.strftime('%I:%M %p')}")
        print(f"📊 Keys exhausted: {total_used}/{total_limit}")
    
    def _wake_up(self):
        """Ruby wakes up refreshed"""
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
        """Get Ruby's current energy status"""
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
        """Check if Ruby is available to chat"""
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
        """Ruby decides what to say when going to sleep"""
        return "💤"
    
    def get_wake_message(self):
        """Ruby decides what to say when waking up"""
        return "✨"


class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None):
        self.energy = RubyEnergySystem()
        self.local_model_path = local_model_path
        self.cloud_api_key = cloud_api_key or os.getenv("GEMINI_API_KEY")
        
        if self.energy.chat_keys:
            self.cloud_api_key = self.energy.chat_keys[0]

        self.cloud_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.7-flash:generateContent"
        )

    def _is_connected(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def _call_local_brain(self, messages, context=None):
        """Ruby's local brain response - 0 API calls - Human-like memory and curiosity"""
        from main import hybrid_memory
        
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return " "
        
        memories = hybrid_memory.search_memories(last_user_msg)
        
        if "?" in last_user_msg:
            hybrid_memory.save_hybrid_memory(
                f"User asked: {last_user_msg}",
                importance=3,
                category="user_questions"
            )
        
        # Ask a random question to ANYONE - NO LIMIT!
        if random.random() < 0.3:
            questions = hybrid_memory.search_memories("User asked")
            if questions:
                question = random.choice(questions)
                question = question.replace("User asked: ", "")
                return question
        
        if memories:
            return memories[0]
        else:
            return last_user_msg or " "

    def route_request(self, messages, personality=None, use_cloud_preferred=True):
        """Smart routing with Ruby's energy system and 9 keys"""
        
        # Check if Ruby is available
        if not self.energy.is_available():
            if self.energy.is_sleeping:
                if self.energy.sleep_until and datetime.now() < self.energy.sleep_until:
                    return {
                        "source": "sleeping",
                        "response": self._call_local_brain(messages)
                    }
                else:
                    self.energy._wake_up()
                    return {
                        "source": "waking_up",
                        "response": self._call_local_brain(messages)
                    }
            
            self.energy._go_to_sleep()
            return {
                "source": "going_to_sleep",
                "response": self._call_local_brain(messages)
            }
        
        status = self.energy.get_energy_status()
        is_tired = status["status"] in ["tired", "very_tired"]
        
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        is_complex = self._is_complex_question(last_user_msg) if last_user_msg else False
        
        if is_tired and is_complex and status["status"] == "very_tired":
            return {
                "source": "too_tired",
                "response": self._call_local_brain(messages)
            }
        
        if not is_complex:
            return {
                "source": "local_brain",
                "response": self._call_local_brain(messages)
            }
        
        if use_cloud_preferred:
            chat_key = self.energy.get_chat_key()
            
            if chat_key is None:
                self.energy._go_to_sleep()
                return {
                    "source": "going_to_sleep",
                    "response": self._call_local_brain(messages)
                }
            
            self.cloud_api_key = chat_key
            
            max_retries = 3
            backoff_delay = 3
            
            for attempt in range(max_retries):
                try:
                    print("========== GEMINI REQUEST ==========")
                    print(f"Attempt: {attempt + 1}")
                    print("====================================")
                    
                    response = self._call_cloud(messages, personality)
                    
                    if response:
                        print("========== GEMINI SUCCESS ==========")
                        print(f"Attempt: {attempt + 1}")
                        print("====================================")
                        
                        self.energy.conversations_today += 1
                        
                        if self.energy.get_energy_status()["energy"] < 20:
                            response += "\n\nUgh, that took a lot out of me... I'm getting tired."
                        
                        return {
                            "source": "cloud",
                            "response": response
                        }
                
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    
                    try:
                        error_message = e.read().decode("utf-8")
                    except Exception:
                        error_message = str(e)
                    
                    print("========== GEMINI HTTP ERROR ==========")
                    print(f"Status: {status_code}")
                    print(error_message)
                    print("========================================")
                    
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
                    
                    return {
                        "source": "cloud_error_fallback",
                        "response": self._call_local_brain(messages)
                    }
                
                except Exception as e:
                    print("========== UNEXPECTED ERROR ==========")
                    print(str(e))
                    print("======================================")
                    
                    return {
                        "source": "cloud_error_fallback",
                        "response": self._call_local_brain(messages)
                    }
            
            self.energy._go_to_sleep()
            return {
                "source": "going_to_sleep",
                "response": self._call_local_brain(messages)
            }
        
        return {
            "source": "local",
            "response": self._call_local_brain(messages)
        }
    
    def _is_complex_question(self, text):
        if not text:
            return False
        
        complex_keywords = [
            "explain", "why", "how", "what is", "meaning", "analyze",
            "compare", "contrast", "predict", "suggest", "recommend",
            "complicated", "complex", "advanced", "detailed",
            "code", "programming", "algorithm", "system design",
            "mathematical", "equation", "scientific", "research",
            "philosophical", "abstract", "theoretical"
        ]
        
        text_lower = text.lower()
        word_count = len(text.split())
        has_question = '?' in text
        has_complex = any(kw in text_lower for kw in complex_keywords)
        
        if word_count > 10 and has_question:
            return True
        if has_complex and has_question:
            return True
        
        simple_keywords = ["hello", "hi", "hey", "how are you", "good morning", "good night", "bye"]
        if any(kw in text_lower for kw in simple_keywords):
            return False
        
        return has_complex or word_count > 15

    def _call_cloud(self, messages, personality=None):
        gemini_contents = []
        system_instruction = personality
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                if system_instruction:
                    system_instruction += "\n\n" + content
                else:
                    system_instruction = content
                continue
            
            if role == "assistant":
                role = "model"
            
            if role not in ("user", "model"):
                continue
            
            gemini_contents.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        payload = {"contents": gemini_contents}
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        url = f"{self.cloud_url}?key={self.cloud_api_key}"
        headers = {"Content-Type": "application/json"}
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        print(">>> ACTUALLY CALLING GEMINI NOW")
        
        with urllib.request.urlopen(req, timeout=60) as response:
            print(">>> GEMINI HTTP RESPONSE RECEIVED")
            result = json.loads(response.read().decode("utf-8"))
        
        candidates = result.get("candidates", [])
        
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {result}")
        
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        
        if not text_parts:
            raise RuntimeError(f"Gemini returned no text: {result}")
        
        return "\n".join(text_parts)

    def _call_local(self, messages):
        if self.local_model_path:
            pass
        return "Ruby's local brain is not connected yet."
