# tools/vision.py
import os
import torch
from PIL import Image
from transformers import AutoModel, AutoProcessor

class VisionEngine:
    """Ruby's vision engine using MiniCPM-V 2.6"""
    
    def __init__(self, model_name="openbmb/MiniCPM-V-2_6"):
        print("🔄 Loading MiniCPM-V... (first time will download ~1.5 GB)")
        self.model_name = model_name
        
        try:
            self.processor = AutoProcessor.from_pretrained(
                model_name, 
                trust_remote_code=True
            )
            self.model = AutoModel.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            print("✅ Vision Engine ready!")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            print("📥 Trying to download model...")
            self._download_model()
    
    def _download_model(self):
        """Download model on first run"""
        print("📥 Downloading MiniCPM-V (this may take 5-10 minutes)...")
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModel.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        print("✅ Model downloaded and loaded!")
    
    def describe_image(self, image_path: str) -> str:
        """Generate a description of an image"""
        try:
            if not os.path.exists(image_path):
                return "Image file not found."
            
            image = Image.open(image_path)
            prompt = "Describe this image in one short sentence."
            
            # Process
            inputs = self.processor(
                images=image,
                text=prompt,
                return_tensors="pt"
            )
            
            # Generate
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=False,
                temperature=0.0
            )
            
            # Decode response
            description = self.processor.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # Clean up
            if prompt in description:
                description = description.replace(prompt, "").strip()
            return description
            
        except Exception as e:
            print(f"⚠️ Vision error: {e}")
            return "I couldn't describe this image."
    
    def describe_from_url(self, image_url: str) -> str:
        """Download and describe an image from URL"""
        try:
            import requests
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return "Couldn't fetch image from URL."
            
            temp_path = "temp_image.jpg"
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            result = self.describe_image(temp_path)
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
        except Exception as e:
            return f"Couldn't fetch image: {e}"
