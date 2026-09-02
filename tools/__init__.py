# tools/__init__.py
# Tools module initialization
# Safe imports with fallbacks for missing modules

__all__ = []

# Try importing each tool, skip if it fails
try:
    from tools.browser import BrowserToolServer
    __all__.append('BrowserToolServer')
except Exception as e:
    print(f"⚠️ Could not import BrowserToolServer: {e}")

try:
    from tools.data_ingestion import DataIngestion
    __all__.append('DataIngestion')
except Exception as e:
    print(f"⚠️ Could not import DataIngestion: {e}")

try:
    from tools.instagram_connector import InstagramConnector
    __all__.append('InstagramConnector')
except Exception as e:
    print(f"⚠️ Could not import InstagramConnector: {e}")

try:
    from tools.video_learner import VideoLearner
    __all__.append('VideoLearner')
except Exception as e:
    print(f"⚠️ Could not import VideoLearner: {e}")

try:
    from tools.web_learner import WebLearner
    __all__.append('WebLearner')
except Exception as e:
    print(f"⚠️ Could not import WebLearner: {e}")

try:
    from tools.websocket_handler import WebSocketHandler
    __all__.append('WebSocketHandler')
except Exception as e:
    print(f"⚠️ Could not import WebSocketHandler: {e}")

try:
    from tools.websocket_server import RubyWebSocketServer
    __all__.append('RubyWebSocketServer')
except Exception as e:
    print(f"⚠️ Could not import RubyWebSocketServer: {e}")
