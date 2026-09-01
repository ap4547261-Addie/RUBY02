# config.py
import os

os.environ["GEMINI_API_KEY1"] = "AIzaSy...YOUR_KEY_1"
os.environ["GEMINI_API_KEY2"] = "AIzaSy...YOUR_KEY_2"
os.environ["GEMINI_API_KEY3"] = "AIzaSy...YOUR_KEY_3"
os.environ["GEMINI_API_KEY4"] = "AIzaSy...YOUR_KEY_4"
os.environ["GEMINI_API_KEY5"] = "AIzaSy...YOUR_KEY_5"
os.environ["GEMINI_API_KEY6"] = "AIzaSy...YOUR_KEY_6"
os.environ["GEMINI_API_KEY7"] = "AIzaSy...YOUR_KEY_7"
os.environ["GEMINI_API_KEY8"] = "AIzaSy...YOUR_KEY_8"
os.environ["GEMINI_API_KEY9"] = "AIzaSy...YOUR_KEY_9"

# Fallback key
os.environ["GEMINI_API_KEY"] = "AIzaSy...YOUR_FALLBACK_KEY"

PINECONE_API_KEY = None
PINECONE_INDEX_HOST = None

print("✅ Keys loaded!")
