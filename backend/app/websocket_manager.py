from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Store connections per user_id or profile_id
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        print(f"Client #{client_id} connected. Total connections for client: {len(self.active_connections[client_id])}")


    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                 self.active_connections[client_id].remove(websocket)
                 if not self.active_connections[client_id]: # If list is empty
                     del self.active_connections[client_id]
                     print(f"Client #{client_id} last connection disconnected. Client removed.")
                 else:
                     print(f"Client #{client_id} a connection disconnected. Remaining: {len(self.active_connections[client_id])}")
            else:
                # This can happen if disconnect is called multiple times or on already removed websocket
                print(f"Client #{client_id} websocket not found for disconnect.")
        else:
            print(f"Client #{client_id} not found in active connections for disconnect.")


    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_client(self, message: str, client_id: str):
        if client_id in self.active_connections:
            # Create a copy of the list for iteration, as disconnect can modify it
            connections_to_iterate = list(self.active_connections[client_id])
            for connection in connections_to_iterate:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    # Handle broken connections, remove them
                    print(f"Error sending to client #{client_id} (removing connection): {e}")
                    self.disconnect(connection, client_id) # Basic removal

manager = ConnectionManager()
