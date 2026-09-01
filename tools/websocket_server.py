# tools/websocket_server.py
import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any


class RubyWebSocketServer:
    """
    WebSocket server for Ruby's browser extension communication
    """
    
    def __init__(self, handler, host="localhost", port=8765):
        self.handler = handler
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        self.total_connections = 0
        self.start_time = datetime.now()
        
        print(f"🔌 Ruby WebSocket Server initializing on ws://{host}:{port}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        
        print(f"✅ Ruby WebSocket Server running on ws://{self.host}:{self.port}")
        print(f"📡 Waiting for browser extension connections...")
        
        await self.server.wait_closed
