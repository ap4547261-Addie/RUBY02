import os
from google import genai
from google.genai import types
from datetime import datetime

class RubyBrainCore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def generate_image(self, prompt_text: str) -> str:
        """Handles image generation using a valid supported model endpoint."""
        try:
            response = self.client.models.generate_content(
                model="imagen-3.0-generate-002",
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspectRatio="1:1"
                    )
                )
            )
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    file_name = f"ruby_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(file_name, "wb") as f:
                        f.write(image_bytes)
                    return file_name
        except Exception as e:
            print(f"Image Gen Error: {e}")
        return None
        
