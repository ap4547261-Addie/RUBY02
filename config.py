# config.py
# Configuration for Ruby App
# Load from environment variables

import os

# ============================================
# GEMINI API KEYS (9 keys support)
# ============================================
# Set these environment variables before running:
# export GEMINI_API_KEY=your_key (primary key)
# export GEMINI_API_KEY1=key1
# export GEMINI_API_KEY2=key2
# ... up to GEMINI_API_KEY9

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================
# PINECONE CONFIGURATION (Optional)
# ============================================
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST", "")

# ============================================
# DATABASE PATHS
# ============================================
SQLITE_PATH = os.getenv("FLET_APP_STORAGE_DATA", ".") + "/ruby_memory.db"
KNOWLEDGE_DB = os.getenv("FLET_APP_STORAGE_DATA", ".") + "/ruby_knowledge.db"
CHAT_HISTORY_FILE = os.getenv("FLET_APP_STORAGE_DATA", ".") + "/ruby_chat_history.json"

# ============================================
# APP SETTINGS
# ============================================
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
LOG_FILE = os.getenv("FLET_APP_STORAGE_DATA", ".") + "/ruby.log"
