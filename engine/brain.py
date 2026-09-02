# engine/brain.py
import os
import threading
from datetime import datetime
from google import genai
from google.genai import types

class RubyBrainCore:
    def __init__(self, api_key=None):
        """Initialize Ruby's brain with 9-key support"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Load all 9 keys from environment
        self.chat_keys = []
        self.image_keys = []
        
        # Keys 1-4 for chat/complex questions
        for i in range(1, 5):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.chat_keys.append(key)
        
        # Keys 5-9 for image generation
        for i in range(5, 10):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.image_keys.append(key)
        
        # Fallback if no keys found
        if not self.chat_keys and not self.image_keys:
            if self.api_key:
                self.chat_keys = [self.api_key]
                self.image_keys = [self.api_key]
        
        # Initialize clients (lazy loading)
        self._chat_clients = {}
        self._image_clients = {}
        self._lock = threading.Lock()
        
        # Track key usage (REQUIRED for API limits)
        self.chat_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.chat_keys}
        self.image_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.image_keys}
        
        self.chat_index = 0
        self.image_index = 0
        
        print(f"RubyBrainCore initialized with {len(self.chat_keys)} chat keys and {len(self.image_keys)} image keys")
    
    def _get_chat_key(self):
        """Get available chat key with usage tracking"""
        with self._lock:
            today = datetime.now().date()
            
            # Reset counts for new day
            for key in self.chat_usage:
                if self.chat_usage[key]["day"] != today:
                    self.chat_usage[key]["count"] = 0
                    self.chat_usage[key]["day"] = today
            
            # Find available key (20 limit = Gemini API quota)
            for _ in range(len(self.chat_keys)):
                key = self.chat_keys[self.chat_index]
                if self.chat_usage[key]["count"] < 20:
                    self.chat_usage[key]["count"] += 1
                    self.chat_index = (self.chat_index + 1) % len(self.chat_keys)
                    print(f"Using chat key {key[:10]}... (count: {self.chat_usage[key]['count']}/20)")
                    return key
                self.chat_index = (self.chat_index + 1) % len(self.chat_keys)
            
            # All keys exhausted
            return None
    
    def _get_image_key(self):
        """Get available image key with usage tracking"""
        with self._lock:
            today = datetime.now().date()
            
            # Reset counts for new day
            for key in self.image_usage:
                if self.image_usage[key]["day"] != today:
                    self.image_usage[key]["count"] = 0
                    self.image_usage[key]["day"] = today
            
            # Find available key (20 limit = Gemini API quota)
            for _ in range(len(self.image_keys)):
                key = self.image_keys[self.image_index]
                if self.image_usage[key]["count"] < 20:
                    self.image_usage[key]["count"] += 1
                    self.image_index = (self.image_index + 1) % len(self.image_keys)
                    print(f"Using image key {key[:10]}... (count: {self.image_usage[key]['count']}/20)")
                    return key
                self.image_index = (self.image_index + 1) % len(self.image_keys)
            
            # All keys exhausted
            return None
    
    def _get_chat_client(self, key):
        """Get or create chat client for specific key"""
        if key not in self._chat_clients:
            self._chat_clients[key] = genai.Client(api_key=key)
        return self._chat_clients[key]
    
    def _get_image_client(self, key):
        """Get or create image client for specific key"""
        if key not in self._image_clients:
            self._image_clients[key] = genai.Client(api_key=key)
        return self._image_clients[key]

    def generate_text(self, messages_payload):
        """Handles core text generation with automatic key rotation"""
        chat_key = self._get_chat_key()
        
        if chat_key is None:
            raise Exception("All chat keys exhausted. Ruby needs rest.")
        
        try:
            client = self._get_chat_client(chat_key)
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=messages_payload
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                with self._lock:
                    if chat_key in self.chat_usage:
                        self.chat_usage[chat_key]["count"] = 20
                return self.generate_text(messages_payload)
            raise e

    def generate_image(self, prompt_text: str) -> str:
        """Handles image generation with automatic key rotation"""
        image_key = self._get_image_key()
        
        if image_key is None:
            print("All image keys exhausted.")
            return None
        
        try:
            phone_camera_prompt = (
                "Raw unfiltered smartphone photo, taken on a phone front camera, "
                "natural skin texture with visible pores, casual everyday lighting, "
                "slight digital noise, unpolished candid snapshot, realistic amateur framing, "
                f"no studio lighting, {prompt_text}"
            )
            
            client = self._get_image_client(image_key)
            
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=phone_camera_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    output_mime_type="image/png"
                )
            )
            
            for generated_image in result.generated_images:
                image_bytes = generated_image.image.image_bytes
                file_name = f"ruby_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(file_name, "wb") as f:
                    f.write(image_bytes)
                return file_name
                
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                with self._lock:
                    if image_key in self.image_usage:
                        self.image_usage[image_key]["count"] = 20
                return self.generate_image(prompt_text)
            
            print(f"Image Gen Error: {e}")
            return None

    def generate_video(self, prompt_text: str) -> str:
        """Handles video generation (placeholder)"""
        try:
            phone_video_prompt = (
                "Raw smartphone video recording, handheld phone camera view, "
                "slight natural hand shake, minor motion jitter, everyday indoor lighting, "
                "unfiltered mobile camera quality, realistic amateur framing, "
                f"no cinematic studio lighting, {prompt_text}"
            )
            print(f"Generating video with prompt: {phone_video_prompt}")
            return None
        except Exception as e:
            print(f"Video Gen Error: {e}")
            return None
    
    def get_usage_stats(self):
        """Get current usage statistics"""
        chat_used = sum(self.chat_usage[key]["count"] for key in self.chat_keys)
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        
        return {
            "chat_keys": len(self.chat_keys),
            "image_keys": len(self.image_keys),
            "chat_used": chat_used,
            "chat_limit": len(self.chat_keys) * 20,
            "image_used": image_used,
            "image_limit": len(self.image_keys) * 20,
            "total_used": chat_used + image_used,
            "total_limit": (len(self.chat_keys) + len(self.image_keys)) * 20,
            "remaining": (len(self.chat_keys) + len(self.image_keys)) * 20 - (chat_used + image_used)
        }
    
    def reset_keys(self):
        """Reset all key usage (called when Ruby wakes up)"""
        today = datetime.now().date()
        with self._lock:
            for key in self.chat_usage:
                self.chat_usage[key]["count"] = 0
                self.chat_usage[key]["day"] = today
            for key in self.image_usage:
                self.image_usage[key]["count"] = 0
                self.image_usage[key]["day"] = today
        
        print("All keys reset! Ruby is refreshed.")
