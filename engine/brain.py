# =====================================================================
# engine/brain.py - 100% Offline Local Version (Google/Imagen Removed)
# =====================================================================

import os
import threading
from datetime import datetime

# Try to import config (optional)
try:
    import config
except ImportError:
    config = None

class RubyBrainCore:
    def __init__(self, api_key=None):
        self.chat_keys = []
        self.image_keys = []
        self._lock = threading.Lock()
        
        print("RubyBrainCore initialized in 100% Local/Offline Mode.")

    def _get_image_key(self):
        return None

    def generate_image(self, prompt_text: str) -> str:
        """Offline fallback: Image generation requires cloud APIs, returning placeholder notice."""
        print(f"🖼️ Image generation requested offline: '{prompt_text}' (Cloud API disabled)")
        return None

    def generate_video(self, prompt_text: str) -> str:
        """Video generation placeholder"""
        print(f"🎬 Video generation requested: {prompt_text}")
        return None

    def get_usage_stats(self):
        return {
            "image_keys": 0,
            "image_used": 0,
            "image_limit": 0,
            "remaining": 0
        }

    def reset_keys(self):
        print("Offline mode: No keys to reset.")
        
