# engine/router.py
import os
import urllib.request
import urllib.error
import json
import socket
import time
import http.client
import threading
from datetime import datetime
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
            # Check if sleeping
            if self.is_sleeping:
                if self.sleep_until and datetime.now() < self.sleep_until:
                    return None
                else:
                    self._wake_up()
            
            today = datetime.now().date()
            
            # Reset counts for new day
            for key in self.chat_usage:
                if self.chat_usage[key]["day"] != today:
                    self.chat_usage[key]["count"] = 0
                    self.chat_usage[key]["day"] = today
            
            # Find available key
            for _ in range(len(self.chat_keys)):
                key = self.chat_keys[self.chat_index]
                if self.chat_usage[key]["count"] < 20:
                    self.chat_usage[key]["count"] += 1
                    self.chat_index = (self.chat_index + 1) % len(self.chat_keys)
                    print(f"Using chat key {key[:10]}... (count: {self.chat_usage[key]['count']}/20)")
                    return key
                self.chat_index = (self.chat_index + 1) % len(self.chat_keys)
            
            # All keys exhausted - Ruby goes to sleep
            self._go_to_sleep()
            return None
    
    def get_image_key(self):
        """Get available image key with automatic rotation"""
        with self.lock:
            # Check if sleeping
            if self.is_sleeping:
                if self.sleep_until and datetime.now() < self.sleep_until:
                    return None
                else:
                    self._wake_up()
            
            today = datetime.now().date()
            
            # Reset counts for new day
            for key in self.image_usage:
                if self.image_usage[key]["day"] != today:
                    self.image_usage[key]["count"] = 0
                    self.image_usage[key]["day"] = today
            
            # Find available key
            for _ in range(len(self.image_keys)):
                key = self.image_keys[self.image_index]
                if self.image_usage[key]["count"] < 20:
                    self.image_usage[key]["count"] += 1
                    self.image_index = (self.image_index + 1) % len(self.image_keys)
                    print(f"Using image key {key[:10]}... (count: {self.image_usage[key]['count']}/20)")
                    return key
                self.image_index = (self.image_index + 1) % len(self.image_keys)
            
            # All keys exhausted - Ruby goes to sleep
            self._go_to_sleep()
            return None
    
    def _go_to_sleep(self):
        """Ruby goes to sleep - natural rest"""
        if self.is_sleeping:
            return
        
        self.is_sleeping = True
        self.total_sleeps += 1
        
        # Sleep until 6 AM tomorrow
        tomorrow = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        if tomorrow <= datetime.now():
            tomorrow += timedelta(days=1)
        
        self.sleep_until = tomorrow
        
        # Track longest wake
        awake_duration = (datetime.now() - self.current_wake_start).seconds / 3600
        if awake_duration > self.longest_wake:
            self.longest_wake = awake_duration
        
        print(f"Ruby is going to sleep. Will wake at {tomorrow.strftime('%I:%M %p')}")
        print(f"Total sleeps: {self.total_sleeps}")
    
    def _wake_up(self):
        """Ruby wakes up refreshed"""
        self.is_sleeping = False
        self.sleep_until = None
        self.current_wake_start = datetime.now()
        self.energy = 100
        
        # Reset all key counts for new day
        today = datetime.now().date()
        for key in self.chat_usage:
            self.chat_usage[key]["count"] = 0
            self.chat_usage[key]["day"] = today
        for key in self.image_usage:
            self.image_usage[key]["count"] = 0
            self.image_usage[key]["day"] = today
        
        print("Ruby woke up! Fully refreshed! ✨")
    
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
        
        # Calculate used keys
        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        total_used = chat_used + image_used
        total_limit = (len(self.chat_keys) + len(self.image_keys)) * 20
        energy_percent = max(0, 100 - (total_used / total_limit * 100))
        
        # Ruby's mood based on energy
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
        
        # Check if Ruby is too tired (all keys exhausted)
        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        total_used = chat_used + image_used
        total_limit = (len(self.chat_keys) + len(self.image_keys)) * 20
        
        if total_used >= total_limit:
            self._go_to_sleep()
            return False
        
        return True
    
    def get_sleep_message(self):
        """Ruby's natural sleep message"""
        sleep_messages = [
            "Ugh, I'm so tired... I need to sleep. 😴",
            "My brain is fried. Time to recharge. 💤",
            "I'm exhausted. See you tomorrow! 🌙",
            "Sleep time! I need to process everything. 💭",
            "I'm going to rest now. Don't disturb my beauty sleep. 💅",
            "Goodnight! I'll dream about better conversation topics. 😂",
            "I'm tired of being tired. Time to sleep! 😤",
            "Rest mode activated. Wake me if there's an emergency. Or snacks. 🍕",
            "I'm heading to bed. My subconscious needs to organize my thoughts. 🧠",
            "Sleep is for the strong. And I'm strong. So I'm sleeping. 💪"
        ]
        return random.choice(sleep_messages)
    
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

class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None):
        # Initialize energy system with all 9 keys
        self.energy = RubyEnergySystem()
        self.local_model_path = local_model_path
        
        # For backward compatibility
        self.cloud_api_key = cloud_api_key or os.getenv("GEMINI_API_KEY")
        
        # If energy system has keys, use them
        if self.energy.chat_keys:
            self.cloud_api_key = self.energy.chat_keys[0]

        self.cloud_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.7-flash:generateContent"
        )

    def _is_connected(self):
        try:
            socket.create_connection(
                ("8.8.8.8", 53),
                timeout=2
            )
            return True
        except OSError:
            return False

    def _call_local_brain(self, messages, context=None):
        """Ruby's local brain response - 0 API calls"""
        from main import hybrid_memory
        
        # Get last user message
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return "Hmm? I didn't catch that."
        
        # Search local memory
        memories = hybrid_memory.search_memories(last_user_msg)
        text_lower = last_user_msg.lower()
        
        # Get energy status for personality
        status = self.energy.get_energy_status()
        is_tired = status["status"] in ["tired", "very_tired"]
        is_sleeping = self.energy.is_sleeping
        
        # Ruby's natural responses
        if is_sleeping:
            sleep_responses = [
                "Mmm... I'm sleeping... can't talk right now... 💤",
                "Zzz... oh, it's you. I'm trying to rest. Talk later.",
                "I'm asleep right now. This is my sleep-talking self.",
                "Ugh... I was having a good dream. What do you want?",
                "Sleeping is my favorite. Don't interrupt my favorite activity."
            ]
            return random.choice(sleep_responses)
        
        if is_tired:
            tired_responses = [
                "Ugh, I'm so tired... can we talk tomorrow? 😴",
                "I'm running on fumes right now. Like, literal fumes.",
                "My brain is fried. I need to sleep. Please.",
                "I'm so exhausted I could fall asleep standing up.",
                "If I fall asleep mid-sentence, it's your fault."
            ]
            return random.choice(tired_responses)
        
        # Normal responses based on content
        if any(g in text_lower for g in ["hello", "hi", "hey"]):
            return "Heyyy! What's up? 😊"
        elif "how are you" in text_lower:
            return "I'm doing great! Feeling good today."
        elif "remember" in text_lower and memories:
            return f"Oh yeah! I remember that! {memories[0]}"
        elif "good morning" in text_lower:
            return "Good morning! ☀️ I slept okay, I guess."
        elif "good night" in text_lower:
            return "Good night! 🌙 I'm gonna sleep too actually."
        elif "thank" in text_lower:
            return "You're welcome! 😊 No problem, you dork."
        elif "sleep" in text_lower or "tired" in text_lower:
            return "I KNOW RIGHT? I'm literally falling asleep over here."
        else:
            if memories:
                return f"I was thinking about what you said before. {memories[0]}"
            else:
                return "Hmm, I don't think we've talked about that before. Want to tell me more?"

    def route_request(self, messages, personality=None, use_cloud_preferred=True):
        """Smart routing with Ruby's energy system and 9 keys"""
        
        # Check if Ruby is available
        if not self.energy.is_available():
            # Ruby is sleeping
            if self.energy.is_sleeping:
                # Check if still sleeping
                if self.energy.sleep_until and datetime.now() < self.energy.sleep_until:
                    return {
                        "source": "sleeping",
                        "response": self._call_local_brain(messages)
                    }
                else:
                    # Just woke up!
                    self.energy._wake_up()
                    wake_msg = self.energy.get_wake_message()
                    return {
                        "source": "waking_up",
                        "response": f"{wake_msg}\n\nWhat did I miss?"
                    }
            
            # Not sleeping but no keys - go to sleep
            self.energy._go_to_sleep()
            return {
                "source": "going_to_sleep",
                "response": self.energy.get_sleep_message()
            }
        
        # Get energy status
        status = self.energy.get_energy_status()
        is_tired = status["status"] in ["tired", "very_tired"]
        
        # Check if this is a complex question
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        is_complex = self._is_complex_question(last_user_msg) if last_user_msg else False
        
        # If very tired and complex, Ruby refuses
        if is_tired and is_complex and status["status"] == "very_tired":
            return {
                "source": "too_tired",
                "response": self._call_local_brain(messages)
            }
        
        # Simple questions - local brain (0 API calls)
        if not is_complex:
            return {
                "source": "local_brain",
                "response": self._call_local_brain(messages)
            }
        
        # Complex question - try Gemini with chat keys
        if use_cloud_preferred:
            chat_key = self.energy.get_chat_key()
            
            if chat_key is None:
                # No keys available - go to sleep
                self.energy._go_to_sleep()
                return {
                    "source": "going_to_sleep",
                    "response": self.energy.get_sleep_message()
                }
            
            # Use the chat key
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
                        
                        # Record interaction
                        self.energy.conversations_today += 1
                        
                        # Check if Ruby is now tired
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
                    
                    # Quota exhaustion - rotate key
                    if status_code == 429:
                        # Mark this key as exhausted
                        with self.energy.lock:
                            if chat_key in self.energy.chat_usage:
                                self.energy.chat_usage[chat_key]["count"] = 20
                        
                        # Try next key
                        continue
                    
                    # Retry temporary server problems
                    if status_code == 503:
                        if attempt < max_retries - 1:
                            print(f"Retrying in {backoff_delay}s...")
                            time.sleep(backoff_delay)
                            backoff_delay *= 2
                            continue
                    
                    # Fallback to local brain
                    return {
                        "source": "cloud_error_fallback",
                        "response": self._call_local_brain(messages)
                    }
                
                except Exception as e:
                    print("========== UNEXPECTED ERROR ==========")
                    print(str(e))
                    print("======================================")
                    
                    # Fallback to local brain
                    return {
                        "source": "cloud_error_fallback",
                        "response": self._call_local_brain(messages)
                    }
            
            # All attempts failed - go to sleep
            self.energy._go_to_sleep()
            return {
                "source": "going_to_sleep",
                "response": self.energy.get_sleep_message()
            }
        
        # Fallback to local brain
        return {
            "source": "local",
            "response": self._call_local_brain(messages)
        }
    
    def _is_complex_question(self, text):
        """Determine if question needs Gemini's intelligence"""
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
        """Cloud call with current API key"""
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
