# engine/brain.py - keeps image generation (Google Imagen), text uses Cloudflare
import os
import threading
from datetime import datetime
from google import genai
from google.genai import types

# Try to import config for Gemini keys (optional, for image generation only)
try:
    import config
except ImportError:
    config = None

class RubyBrainCore:
    def __init__(self, api_key=None):
        # Chat keys are not used (text uses Cloudflare)
        self.chat_keys = []
        self.image_keys = []

        # Load image keys (5-9) from environment or config – for Imagen
        for i in range(5, 10):
            key = os.getenv(f"GEMINI_API_KEY{i}")
            if key:
                self.image_keys.append(key)
        if not self.image_keys:
            fallback = os.getenv("GEMINI_API_KEY")
            if fallback:
                self.image_keys = [fallback]
        # Also try config if available
        if config is not None and not self.image_keys:
            for i in range(5, 10):
                key = getattr(config, f"GEMINI_API_KEY{i}", None)
                if key:
                    self.image_keys.append(key)
            if not self.image_keys:
                key = getattr(config, "GEMINI_API_KEY", None)
                if key:
                    self.image_keys = [key]

        self._image_clients = {}
        self._lock = threading.Lock()
        self.image_usage = {key: {"count": 0, "day": datetime.now().date()} for key in self.image_keys}
        self.image_index = 0

        print(f"RubyBrainCore: {len(self.image_keys)} image keys loaded for Imagen.")

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

    def _get_image_client(self, key):
        if key not in self._image_clients:
            self._image_clients[key] = genai.Client(api_key=key)
        return self._image_clients[key]

    def generate_image(self, prompt_text: str) -> str:
        """Handles image generation with automatic key rotation (Imagen)"""
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
        """Video generation placeholder (not implemented)"""
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
        image_used = sum(self.image_usage[key]["count"] for key in self.image_keys)
        return {
            "image_keys": len(self.image_keys),
            "image_used": image_used,
            "image_limit": len(self.image_keys) * 20,
            "remaining": len(self.image_keys) * 20 - image_used
        }

    def reset_keys(self):
        today = datetime.now().date()
        with self._lock:
            for key in self.image_usage:
                self.image_usage[key]["count"] = 0
                self.image_usage[key]["day"] = today
        print("Image keys reset! Ruby is refreshed.")
