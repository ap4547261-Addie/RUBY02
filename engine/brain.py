import os
from google import genai
from google.genai import types
from datetime import datetime

class RubyBrainCore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def generate_image(self, prompt_text: str) -> str:
        """Handles image generation using the correct Imagen client endpoint."""
        try:
            result = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt_text,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
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
