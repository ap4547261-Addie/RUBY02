# engine/brain.py
import os
from google import genai
from google.genai import types
from datetime import datetime

class RubyBrainCore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, messages_payload):
        """Handles core text generation using the Gemini 3.6 Flash model."""
        try:
            # Convert simple dictionary format to contents structure if needed
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=messages_payload
            )
            return response.text
        except Exception as e:
            print(f"Text Gen Error: {e}")
            raise e

    def generate_image(self, prompt_text: str) -> str:
        """Handles image generation using the correct Imagen client endpoint with raw phone-camera styling."""
        try:
            phone_camera_prompt = (
                "Raw unfiltered smartphone photo, taken on a phone front camera, "
                "natural skin texture with visible pores, casual everyday lighting, "
                "slight digital noise, unpolished candid snapshot, realistic amateur framing, "
                f"no studio lighting, {prompt_text}"
            )
            
            result = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=phone_camera_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",  # Optimized for vertical mobile screens
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
            print(f"Image Gen Error: {e}")
        return None

    def generate_video(self, prompt_text: str) -> str:
        """Handles video generation with shaky, unfiltered smartphone camera framing."""
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
