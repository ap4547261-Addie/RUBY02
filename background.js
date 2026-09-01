# tools/websocket_server.py - NEW FILE
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
        
        # Keep server running
        await self.server.wait_closed()
    
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        client_id = self.total_connections + 1
        self.total_connections += 1
        self.clients.add(websocket)
        
        print(f"🔗 Client #{client_id} connected from {websocket.remote_address}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Ruby's brain! 🧠",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    # Parse JSON message
                    data = json.loads(message)
                    
                    # Process through handler
                    if self.handler:
                        await self.handler.handle_message(data)
                    
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "type": "acknowledgment",
                        "message": "Data received and processed ✅",
                        "timestamp": datetime.now().isoformat(),
                        "platform": data.get("platform", "unknown"),
                        "content_length": len(data.get("content", ""))
                    }))
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON from client #{client_id}: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "error": str(e)
                    }))
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Error processing message",
                        "error": str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed as e:
            print(f"🔌 Client #{client_id} disconnected: {e}")
        except Exception as e:
            print(f"❌ Client #{client_id} error: {e}")
        finally:
            self.clients.remove(websocket)
            print(f"📊 Active connections: {len(self.clients)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message_str)
            except Exception:
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.remove(client)
    
    async def send_to_client(self, client_id: int, message: Dict[str, Any]):
        """Send message to specific client"""
        # Find client by ID (would need to store mapping)
        # For now, broadcast to all
        await self.broadcast(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "status": "running" if self.server else "stopped",
            "host": self.host,
            "port": self.port,
            "active_connections": len(self.clients),
            "total_connections": self.total_connections,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }

# Singleton instance
_websocket_server = None

def get_websocket_server(handler=None, host="localhost", port=8765):
    """Get or create WebSocket server instance"""
    global _websocket_server
    if _websocket_server is None:
        _websocket_server = RubyWebSocketServer(handler, host, port)
    return _websocket_server
