import threading
import asyncio
import flet as ft
from engine.brain import main_app_ui
from tools.browser import BrowserToolServer

def start_background_websocket():
    """Runs the asynchronous WebSocket server in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def handle_incoming_browser_data(platform, content):
        # This callback handles streamed data coming from your Chrome extension
        print(f"[WebSocket Bridge] Received content from {platform}: {content[:100]}...")

    server = BrowserToolServer(host="localhost", port=8765, on_message_callback=handle_incoming_browser_data)
    loop.run_until_complete(server.start_server())

def main(page: ft.Page):
    # Pass the page directly into your core Flet UI layout
    main_app_ui(page)

if __name__ == "__main__":
    # Spin up the browser tool WebSocket listener in a background thread
    ws_thread = threading.Thread(target=start_background_websocket, daemon=True)
    ws_thread.start()

    # Start the Flet application interface
    ft.app(target=main)
