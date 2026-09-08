# engine/brain.py - no config.py, only environment variables
import os
import threading
from datetime import datetime
from google import genai
from google.genai import types

class RubyBrainCore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        self.chat_keys = []
        self.image_keys = []

        for i in range(1, 5):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.chat_keys.append(key)

        for i in range(5, 10):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.image_keys.append(key)

        if not self.chat_keys and not self.image_keys:
            if self.api_key:
                self.chat_keys = [self.api_key]
                self.image_keys = [self.api_key]

        self._chat_clients = {}
        self._image_clients = {}
        self._lock = threading.Lock()

        self.chat_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.chat_keys}
        self.image_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.image_keys}

        self.chat_index = 0
        self.image_index = 0

        print(f"RubyBrainCore initialized with {len(self.chat_keys)} chat keys and {len(self.image_keys)} image keys.")

    def _get_chat_key(self):
        with self._lock:
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

            return None

    def _get_image_key(self):
        with self._lock:
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

            return None

    def _get_chat_client(self, key):
        if key not in self._chat_clients:
            self._chat_clients[key] = genai.Client(api_key=key)
        return self._chat_clients[key]

    def _get_image_client(self, key):
        if key not in self._image_clients:
            self._image_clients[key] = genai.Client(api_key=key)
        return self._image_clients[key]

    def generate_text(self, messages_payload):
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
        print(f"Generating video with prompt: {prompt_text}")
        return None

    def get_usage_stats(self):
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
        today = datetime.now().date()
        with self._lock:
            for key in self.chat_usage:
                self.chat_usage[key]["count"] = 0
                self.chat_usage[key]["day"] = today
            for key in self.image_usage:
                self.image_usage[key]["count"] = 0
                self.image_usage[key]["day"] = today
        print("All keys reset! Ruby is refreshed.")
