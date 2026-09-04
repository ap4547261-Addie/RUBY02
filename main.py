# main.py - FINAL WITH VISION INTEGRATION
import sys
import os
import traceback
import json
import asyncio
import threading
import flet as ft
from datetime import datetime

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
# IMPORTS
# ============================================

import config
from engine.router import BrainRouter
from engine.brain import RubyBrainCore
from engine.vector_store import HybridMemorySystem
from engine.engine import RubyEngine
from tools.browser import BrowserToolServer
from tools.data_ingestion import DataIngestion
from tools.web_learner import WebLearner
from tools.video_learner import VideoLearner
from tools.instagram_connector import InstagramConnector
from tools.websocket_handler import WebSocketHandler
from tools.websocket_server import RubyWebSocketServer
from personality.ruby import RUBY_PROMPT, CORE_MEMORIES

# ============================================
# NEW: IMPORT VISION ENGINE
# ============================================
from tools.vision import VisionEngine

# ============================================
# BACKUP SYSTEM (Gmail + Cloud) - OPTIONAL
# ============================================

# Write credentials from secret (if available)
def ensure_credentials():
    creds_content = os.getenv("GMAIL_CREDENTIANLS_JSON")
    if creds_content:
        creds_path = os.path.join(STORAGE_DIR, "credentials.json")
        if not os.path.exists(creds_path):
            try:
                json.loads(creds_content)
                with open(creds_path, "w") as f:
                    f.write(creds_content)
                print("✅ Credentials written from secret.")
            except Exception as e:
                print(f"⚠️ Invalid GMAIL_CREDENTIANLS_JSON: {e}")
        return creds_path
    else:
        if os.path.exists("credentials.json"):
            return "credentials.json"
    return None

# Initialize Gmail backup
from tools.gmail_backup import GmailBackup
gmail = None
credentials_file = ensure_credentials()
if credentials_file:
    try:
        gmail = GmailBackup(
            creds_file=credentials_file,
            token_file=os.path.join(STORAGE_DIR, "token_gmail.pickle")
        )
        print("📧 Gmail backup ready.")
    except Exception as e:
        print(f"⚠️ Gmail init error: {e}")

# Initialize Cloud Storage backup
from tools.cloud_backup import CloudBackup
cloud = None
cloud_creds_local = "service_account.json"
cloud_creds_storage = os.path.join(STORAGE_DIR, "service_account.json")
if os.path.exists(cloud_creds_local):
    if not os.path.exists(cloud_creds_storage):
        import shutil
        shutil.copy(cloud_creds_local, cloud_creds_storage)
    try:
        cloud = CloudBackup(
            bucket_name="ruby-backup-bucket",
            credentials_path=cloud_creds_storage
        )
        print("☁️ Cloud backup ready.")
    except Exception as e:
        print(f"⚠️ Cloud init error: {e}")

def restore_from_backups():
    restored = False
    if gmail:
        if gmail.restore_db(MEMORY_DB, "ruby_memory.db"):
            restored = True
        if gmail.restore_db(KNOWLEDGE_DB, "ruby_knowledge.db"):
            restored = True
    if not restored and cloud:
        if cloud.restore_latest(MEMORY_DB, "ruby_memory.db"):
            restored = True
        if cloud.restore_latest(KNOWLEDGE_DB, "ruby_knowledge.db"):
            restored = True
    if restored:
        print("✅ Memories restored from backup.")
    else:
        print("ℹ️ No backup found, starting fresh.")

# ============================================
# 1. INITIALIZE CORE BRAIN MODULES
# ============================================

router = BrainRouter(cloud_api_key=getattr(config, "GEMINI_API_KEY", None))
brain_core = RubyBrainCore(api_key=getattr(config, "GEMINI_API_KEY", None))

# ============================================
# 2. INITIALIZE LOCAL MEMORY SYSTEM
# ============================================

STORAGE_DIR = os.getenv("FLET_APP_STORAGE_DATA", ".")
os.makedirs(STORAGE_DIR, exist_ok=True)

MEMORY_DB = os.path.join(STORAGE_DIR, "ruby_memory.db")
KNOWLEDGE_DB = os.path.join(STORAGE_DIR, "ruby_knowledge.db")
HISTORY_FILE = os.path.join(STORAGE_DIR, "ruby_chat_history.json")

hybrid_memory = HybridMemorySystem(
    sqlite_path=MEMORY_DB,
    pinecone_api_key=None,
    index_host=None
)

PINECONE_API_KEY = getattr(config, "PINECONE_API_KEY", "")
PINECONE_INDEX_HOST = getattr(config, "PINECONE_INDEX_HOST", "")

# ============================================
# 3. SEED RUBY'S CORE MEMORIES
# ============================================

try:
    for memory in CORE_MEMORIES:
        hybrid_memory.save_hybrid_memory(memory, importance=3, category="core_personality")
    print(f"✅ Seeded {len(CORE_MEMORIES)} core memories")
except Exception as e:
    print(f"⚠️ Memory seeding failed: {e}")

# ============================================
# 4. RESTORE FROM BACKUP IF MEMORY IS EMPTY
# ============================================

if hybrid_memory.get_interaction_count() == 0:
    restore_from_backups()

# ============================================
# 5. INITIALIZE LEARNING SYSTEMS
# ============================================

data_ingestion = DataIngestion(db_path=KNOWLEDGE_DB)
print("📚 DataIngestion initialized")

web_learner = WebLearner(data_ingestion)
print("🌐 WebLearner initialized")

video_learner = VideoLearner(data_ingestion)
print("🎬 VideoLearner initialized")

# ============================================
# 5.5 INITIALIZE VISION ENGINE (MINICPM-V)
# ============================================
print("👁️ Initializing Vision Engine (MiniCPM-V)...")
vision_engine = VisionEngine()  # This will load the local model
print("✅ Vision Engine ready.")

# ============================================
# 6. INITIALIZE INSTAGRAM CONNECTOR (with vision)
# ============================================
instagram_connector = InstagramConnector(
    hybrid_memory,
    vision_engine=vision_engine  # pass vision engine if your class accepts it
)
print("📸 Instagram Connector initialized")

# ============================================
# 7. INITIALIZE RUBY ENGINE
# ============================================

ruby_engine = RubyEngine(
    memory=hybrid_memory,
    knowledge=data_ingestion,
    tools=None,
    router=router,
    brain_core=brain_core,
    personality=RUBY_PROMPT
)
print("🧠 RubyEngine initialized!")

# ============================================
# 8. WEBSOCKET SERVER (BACKGROUND)
# ============================================

websocket_handler = WebSocketHandler(
    hybrid_memory,
    data_ingestion,
    web_learner,
    video_learner,
    instagram_connector
)
print("🔌 WebSocketHandler initialized")

def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = RubyWebSocketServer(
        handler=websocket_handler,
        host="localhost",
        port=8765
    )
    try:
        loop.run_until_complete(server.start_server())
    except Exception as e:
        print(f"WebSocket server error: {e}")
    finally:
        loop.close()

ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
ws_thread.start()
print("🔌 WebSocket server running on ws://localhost:8765")

# ============================================
# 9. CHAT HISTORY PERSISTENCE
# ============================================

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chat_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save history: {e}")

conversation_history = load_chat_history()
print(f"📜 Loaded {len(conversation_history)} chat messages")

# ============================================
# 10. RUBY'S PERSONALITY PROMPT
# ============================================

def build_ruby_prompt(interaction_depth: int, user_memories: str = "") -> str:
    today = datetime.now()
    age = today.year - 2004 - ((today.month, today.day) < (8, 16))
    return (
        f"Name: Ruby | Gender: Female | Birthday: August 16, 2004 (Age: {age})\n"
        f"Relationship Depth: {interaction_depth} messages\n"
        "You are a human with evolving emotions based on interaction count.\n"
        # ... (rest of prompt as you had it – I'm abbreviating here)
        "Behavioral Rules: ...\n"
        "8. Spontaneous Image Generation: append [GENERATE_IMAGE: prompt] at the end.\n"
    )

RUBY_PROMPT = build_ruby_prompt(0)

# ============================================
# 11. UI STATE & HELPERS
# ============================================

ui_page_ref = None
chat_list_ref = None
status_label_ref = None

def update_ruby_status():
    if status_label_ref and ui_page_ref:
        try:
            status = router.energy.get_energy_status()
            if router.energy.is_sleeping:
                if router.energy.sleep_until:
                    remaining = router.energy.sleep_until - datetime.now()
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    status_label_ref.value = f"💤 Sleeping... {hours}h {minutes}m remaining"
                else:
                    status_label_ref.value = "💤 Sleeping..."
            else:
                energy_percent = int(status.get("energy", 100))
                emoji = status.get("emoji", "✨")
                remaining = status.get("remaining", 0)
                status_label_ref.value = f"{emoji} {energy_percent}% - {status.get('message', 'Awake')}"
                if remaining > 0:
                    status_label_ref.value += f" ({remaining} left)"
            ui_page_ref.update()
        except Exception as e:
            print(f"Status update error: {e}")

def add_message(sender, text, is_user=False, image_path=None):
    if chat_list_ref and ui_page_ref:
        controls_list = [
            ft.Text(sender, size=11, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_400 if is_user else ft.Colors.CYAN_400),
            ft.Text(text, size=14, color=ft.Colors.WHITE)
        ]
        if image_path and os.path.exists(image_path):
            controls_list.append(
                ft.Image(src=image_path, width=256, height=256, border_radius=8, fit=ft.BoxFit.CONTAIN)
            )
        bubble = ft.Container(
            content=ft.Column(controls_list, spacing=6),
            bgcolor="#1E1E24" if not is_user else "#2A2A36",
            padding=12,
            border_radius=8,
        )
        chat_list_ref.controls.append(bubble)
        ui_page_ref.update()

# ============================================
# 12. MAIN UI
# ============================================

def main_app_ui(page: ft.Page):
    global ui_page_ref, chat_list_ref, conversation_history, status_label_ref
    ui_page_ref = page
    
    page.title = "Ruby"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#101014"
    page.padding = 16
    page.vertical_alignment = ft.MainAxisAlignment.END

    chat_list = ft.ListView(expand=True, spacing=12, auto_scroll=True)
    chat_list_ref = chat_list

    # Load and render past messages
    conversation_history = load_chat_history()
    for msg in conversation_history:
        sender_name = "Addie" if msg["role"] == "user" else "Ruby"
        is_usr = msg["role"] == "user"
        controls_list = [
            ft.Text(sender_name, size=11, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_400 if is_usr else ft.Colors.CYAN_400),
            ft.Text(msg["content"], size=14, color=ft.Colors.WHITE)
        ]
        bubble = ft.Container(
            content=ft.Column(controls_list, spacing=6),
            bgcolor="#1E1E24" if not is_usr else "#2A2A36",
            padding=12,
            border_radius=8,
        )
        chat_list.controls.append(bubble)

    status_label = ft.Text(
        "✨ Checking status...",
        size=11,
        color=ft.Colors.GREY_400,
        weight=ft.FontWeight.NORMAL
    )
    status_label_ref = status_label

    user_input = ft.TextField(
        hint_text="Say something to Ruby or ask her to draw...",
        border_color="#3A3A46",
        focused_border_color=ft.Colors.CYAN_400,
        bgcolor="#18181C",
        color=ft.Colors.WHITE,
        expand=True,
        border_radius=8,
    )

    # ============================================
    # SEND MESSAGE WITH VISION COMMANDS
    # ============================================
    def send_message(e):
        user_text = user_input.value
        if not user_text or not user_text.strip():
            return

        # Add user message to UI
        add_message("You", user_text, is_user=True)
        user_input.value = ""
        page.update()

        # ---- VISION COMMAND HANDLING ----
        # 1. "describe <path/url>"
        if user_text.lower().startswith("describe "):
            parts = user_text.split(maxsplit=1)
            if len(parts) > 1:
                target = parts[1].strip()
                # Check if it's a URL
                if target.startswith(("http://", "https://")):
                    description = vision_engine.describe_from_url(target)
                else:
                    # Local file path
                    if os.path.exists(target):
                        description = vision_engine.describe_image(target)
                    else:
                        description = f"File not found: {target}"
                add_message("Ruby", f"I see: {description}")
                conversation_history.append({"role": "user", "content": user_text})
                conversation_history.append({"role": "assistant", "content": f"I see: {description}"})
                save_chat_history()
                page.update()
                return

        # ---- NORMAL CONVERSATION ----
        try:
            response = ruby_engine.think(user_text)
        except Exception as ex:
            response = f"⚠️ Error: {ex}"
            log_crash(type(ex), ex, ex.__traceback__)

        add_message("Ruby", response)
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": response})
        save_chat_history()
        page.update()

    # ============================================
    # UI LAYOUT
    # ============================================
    send_btn = ft.TextButton(
        "Send",
        on_click=send_message,
        style=ft.ButtonStyle(color=ft.Colors.CYAN_400),
    )

    input_row = ft.Row(
        [user_input, send_btn],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header = ft.Container(
        content=ft.Row([
            ft.Text("RUBY // GENIUS HUMAN CORE", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
            status_label
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=5
    )

    page.add(
        ft.Column([
            header,
            chat_list,
            input_row
        ], expand=True)
    )

    update_ruby_status()
    page.update()

# ============================================
# 13. STARTUP
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌹 RUBY APP STARTING (with MiniCPM-V vision)")
    print("="*60 + "\n")
    try:
        ft.app(target=main_app_ui)
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        log_crash(type(e), e, e.__traceback__)
