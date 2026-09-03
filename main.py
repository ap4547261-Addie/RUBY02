# main.py - FULL CRASH-PROOF VERSION
import sys
import os
import traceback
import threading
import json
import asyncio
from datetime import datetime

import flet as ft

# ============================================
# CRASH LOGGING (MUST BE FIRST)
# ============================================

CRASH_LOG_PATH = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "ruby_crash.txt")

def init_crash_logging():
    try:
        os.makedirs(os.path.dirname(CRASH_LOG_PATH) or ".", exist_ok=True)
        with open(CRASH_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n[APP START] {datetime.now().isoformat()}\n{'='*60}\n")
        print(f"✅ Crash logger: {CRASH_LOG_PATH}")
    except Exception as e:
        print(f"⚠️ Could not init crash logger: {e}")

def log_crash(exc_type, exc_value, exc_tb):
    error = f"\n{'='*60}\n[CRASH] {datetime.now().isoformat()}\n{'='*60}\n"
    error += f"Type: {exc_type.__name__}\nError: {exc_value}\nTraceback:\n"
    error += "".join(traceback.format_tb(exc_tb)) + f"{'='*60}\n"
    try:
        with open(CRASH_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(error)
    except:
        pass
    print(error, file=sys.stderr)

init_crash_logging()
sys.excepthook = log_crash

# ============================================
# SAFE IMPORTS WITH FALLBACKS
# ============================================

# Config
try:
    import config
    GEMINI_API_KEY = getattr(config, "GEMINI_API_KEY", "")
    PINECONE_API_KEY = getattr(config, "PINECONE_API_KEY", "")
    PINECONE_INDEX_HOST = getattr(config, "PINECONE_INDEX_HOST", "")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    GEMINI_API_KEY = PINECONE_API_KEY = PINECONE_INDEX_HOST = ""

# Engine modules
try:
    from engine.router import BrainRouter
    print("✅ BrainRouter imported")
except Exception as e:
    print(f"❌ BrainRouter import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    class BrainRouter:
        def __init__(self, **kwargs):
            self.energy = type('Energy', (), {
                'get_energy_status': lambda: {'energy': 100, 'emoji': '✨', 'message': 'OK'},
                'is_sleeping': False,
                'sleep_until': None
            })()

try:
    from engine.brain import RubyBrainCore
    print("✅ RubyBrainCore imported")
except Exception as e:
    print(f"❌ RubyBrainCore import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    class RubyBrainCore:
        def __init__(self, **kwargs): pass

try:
    from engine.vector_store import HybridMemorySystem
    print("✅ HybridMemorySystem imported")
except Exception as e:
    print(f"❌ HybridMemorySystem import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    class HybridMemorySystem:
        def __init__(self, **kwargs): pass
        def save_hybrid_memory(self, *args, **kwargs): pass
        def get_interaction_count(self): return 0
        def search_memories(self, query): return []

try:
    from engine.engine import RubyEngine
    print("✅ RubyEngine imported")
except Exception as e:
    print(f"❌ RubyEngine import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    class RubyEngine:
        def __init__(self, **kwargs): pass
        def think(self, msg): return "I'm Ruby, your virtual friend."

# Tools
try:
    from tools.data_ingestion import DataIngestion
    print("✅ DataIngestion imported")
except Exception as e:
    print(f"❌ DataIngestion import failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    class DataIngestion:
        def __init__(self, **kwargs): pass
        def search_knowledge(self, query): return []

try:
    from tools.web_learner import WebLearner
    print("✅ WebLearner imported")
except Exception as e:
    print(f"⚠️ WebLearner import failed: {e}")
    class WebLearner:
        def __init__(self, *args, **kwargs): pass

try:
    from tools.video_learner import VideoLearner
    print("✅ VideoLearner imported")
except Exception as e:
    print(f"⚠️ VideoLearner import failed: {e}")
    class VideoLearner:
        def __init__(self, *args, **kwargs): pass

try:
    from tools.instagram_connector import InstagramConnector
    print("✅ InstagramConnector imported")
except Exception as e:
    print(f"⚠️ InstagramConnector import failed: {e}")
    class InstagramConnector:
        def __init__(self, *args, **kwargs): pass

try:
    from tools.websocket_handler import WebSocketHandler
    print("✅ WebSocketHandler imported")
except Exception as e:
    print(f"⚠️ WebSocketHandler import failed: {e}")
    class WebSocketHandler:
        def __init__(self, *args, **kwargs): pass

try:
    from tools.websocket_server import RubyWebSocketServer
    print("✅ RubyWebSocketServer imported")
except Exception as e:
    print(f"⚠️ RubyWebSocketServer import failed: {e}")
    class RubyWebSocketServer:
        def __init__(self, **kwargs): pass
        async def start_server(self): pass

# Personality
try:
    from personality.ruby import RUBY_PROMPT, CORE_MEMORIES
    print("✅ RUBY_PROMPT and CORE_MEMORIES imported")
except Exception as e:
    print(f"⚠️ Personality import failed: {e}")
    RUBY_PROMPT = "You are Ruby, a helpful assistant."
    CORE_MEMORIES = []

# ============================================
# SAFE STORAGE SETUP (Android-friendly)
# ============================================

STORAGE_DIR = os.getenv("FLET_APP_STORAGE_DATA", ".")
os.makedirs(STORAGE_DIR, exist_ok=True)

MEMORY_DB = os.path.join(STORAGE_DIR, "ruby_memory.db")
KNOWLEDGE_DB = os.path.join(STORAGE_DIR, "ruby_knowledge.db")
HISTORY_FILE = os.path.join(STORAGE_DIR, "ruby_chat_history.json")

print(f"📁 Storage: {STORAGE_DIR}")

# ============================================
# INITIALIZE SYSTEMS (WITH ERROR HANDLING)
# ============================================

print("\n🔧 Initializing systems...")

try:
    router = BrainRouter(cloud_api_key=GEMINI_API_KEY)
    print("✅ Router initialized")
except Exception as e:
    print(f"❌ Router init failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    router = BrainRouter()

try:
    brain_core = RubyBrainCore(api_key=GEMINI_API_KEY)
    print("✅ Brain core initialized")
except Exception as e:
    print(f"❌ Brain core init failed: {e}")
    brain_core = RubyBrainCore()

try:
    hybrid_memory = HybridMemorySystem(sqlite_path=MEMORY_DB, pinecone_api_key=None)
    print("✅ Memory system initialized")
except Exception as e:
    print(f"❌ Memory init failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    hybrid_memory = HybridMemorySystem()

# Seed Ruby's core memories
try:
    if CORE_MEMORIES:
        for memory in CORE_MEMORIES:
            hybrid_memory.save_hybrid_memory(memory, importance=3, category="core_personality")
        print(f"✅ Seeded {len(CORE_MEMORIES)} core memories")
except Exception as e:
    print(f"⚠️ Memory seeding failed: {e}")

try:
    data_ingestion = DataIngestion(db_path=KNOWLEDGE_DB)
    print("✅ Data ingestion initialized")
except Exception as e:
    print(f"❌ Data ingestion init failed: {e}")
    data_ingestion = DataIngestion()

try:
    web_learner = WebLearner(data_ingestion)
    print("✅ Web learner initialized")
except Exception as e:
    print(f"⚠️ Web learner init failed: {e}")
    web_learner = WebLearner(data_ingestion)

try:
    video_learner = VideoLearner(data_ingestion)
    print("✅ Video learner initialized")
except Exception as e:
    print(f"⚠️ Video learner init failed: {e}")
    video_learner = VideoLearner(data_ingestion)

try:
    instagram_connector = InstagramConnector(hybrid_memory)
    print("✅ Instagram connector initialized")
except Exception as e:
    print(f"⚠️ Instagram connector init failed: {e}")
    instagram_connector = InstagramConnector(hybrid_memory)

try:
    ruby_engine = RubyEngine(
        memory=hybrid_memory,
        knowledge=data_ingestion,
        tools=None,
        router=router,
        brain_core=brain_core,
        personality=RUBY_PROMPT
    )
    print("✅ Ruby engine initialized")
except Exception as e:
    print(f"❌ Ruby engine init failed: {e}")
    log_crash(type(e), e, e.__traceback__)
    ruby_engine = RubyEngine()

# ============================================
# WEBSOCKET SERVER (NON-BLOCKING)
# ============================================

try:
    websocket_handler = WebSocketHandler(
        hybrid_memory,
        data_ingestion,
        web_learner,
        video_learner,
        instagram_connector
    )
    print("✅ WebSocket handler initialized")

    def start_websocket_server():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server = RubyWebSocketServer(handler=websocket_handler, host="localhost", port=8765)
            loop.run_until_complete(server.start_server())
        except Exception as e:
            print(f"⚠️ WebSocket error: {e}")
        finally:
            loop.close()

    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    print("✅ WebSocket server started")
except Exception as e:
    print(f"⚠️ WebSocket setup failed: {e}")

# ============================================
# CHAT HISTORY
# ============================================

conversation_history = []

def load_chat_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Load history failed: {e}")
    return []

def save_chat_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Save history failed: {e}")

conversation_history = load_chat_history()
print(f"📜 Loaded {len(conversation_history)} chat messages")

# ============================================
# UI SETUP
# ============================================

ui_page_ref = None
chat_list_ref = None
status_label_ref = None

def update_ruby_status():
    if status_label_ref and ui_page_ref:
        try:
            status = router.energy.get_energy_status()
            status_label_ref.value = f"{status.get('emoji', '✨')} {status.get('message', 'Ready')}"
            ui_page_ref.update()
        except Exception as e:
            print(f"Status error: {e}")

def add_message(sender, text, is_user=False, image_path=None):
    if chat_list_ref and ui_page_ref:
        try:
            controls = [
                ft.Text(sender, size=11, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.AMBER_400 if is_user else ft.Colors.CYAN_400),
                ft.Text(text, size=14, color=ft.Colors.WHITE)
            ]
            bubble = ft.Container(
                content=ft.Column(controls, spacing=6),
                bgcolor="#1E1E24" if not is_user else "#2A2A36",
                padding=12,
                border_radius=8,
            )
            chat_list_ref.controls.append(bubble)
            ui_page_ref.update()
        except Exception as e:
            print(f"Add message error: {e}")

# ============================================
# MAIN UI
# ============================================

def main_app_ui(page: ft.Page):
    global ui_page_ref, chat_list_ref, status_label_ref

    try:
        ui_page_ref = page
        page.title = "Ruby"
        page.theme_mode = ft.ThemeMode.DARK
        page.vertical_alignment = ft.MainAxisAlignment.SPACE_BETWEEN

        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("🌹 Ruby", size=24, weight=ft.FontWeight.BOLD),
                status_label_ref := ft.Text("✨ Loading...", size=12)
            ]),
            padding=10,
            bgcolor=ft.Colors.BLUE_GREY_900
        )

        # Chat list
        chat_list_ref = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8)
        chat_area = ft.Container(content=chat_list_ref, expand=True, padding=10)

        # Input row
        msg_input = ft.TextField(label="Message", expand=True)

        def send_message(e):
            if not msg_input.value:
                return
            user_text = msg_input.value
            add_message("You", user_text, is_user=True)
            msg_input.value = ""
            msg_input.focus()
            # Use the real local brain
            try:
                response = ruby_engine.think(user_text)
            except Exception as ex:
                response = f"⚠️ Error: {ex}"
                log_crash(type(ex), ex, ex.__traceback__)
            add_message("Ruby", response)
            # Save history
            conversation_history.append({"role": "user", "content": user_text})
            conversation_history.append({"role": "assistant", "content": response})
            save_chat_history()
            page.update()

        send_btn = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=send_message)
        input_row = ft.Row([msg_input, send_btn], spacing=5)

        page.add(header, chat_area, input_row)

        print("✅ UI loaded successfully!")
        update_ruby_status()

    except Exception as e:
        print(f"❌ UI error: {e}")
        log_crash(type(e), e, e.__traceback__)
        page.add(ft.Text(f"❌ App Error: {str(e)}", color=ft.Colors.RED))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌹 RUBY APP STARTING")
    print("="*60 + "\n")
    try:
        ft.app(target=main_app_ui)
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        log_crash(type(e), e, e.__traceback__)
