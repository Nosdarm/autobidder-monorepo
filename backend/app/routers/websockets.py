from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket_manager import manager
# You'll need a way to get current_user_id, e.g., from token in query params or path
# For simplicity, let's assume client_id (e.g., user_id or profile_id) is part of the path for now.

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/status/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    print(f"Client #{client_id} attempting to connect to WebSocket.") # Added for clarity
    try:
        while True:
            # Keep the connection alive, or receive messages from client if needed
            data = await websocket.receive_text()
            # For now, server doesn't expect messages for this use case,
            # but you can echo or handle if client sends something.
            # Example: log received data or send an ack
            print(f"Client #{client_id} sent: {data}")
            # await manager.send_personal_message(f"Server received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        print(f"Client #{client_id} disconnected")
    except Exception as e:
        # It's good practice to log the exception details
        print(f"Error with client #{client_id} WebSocket: {type(e).__name__} - {e}")
        # Ensure disconnect is called on any other exception
        manager.disconnect(websocket, client_id)
        # Optionally, you might want to close the websocket explicitly if not done by disconnect
        # await websocket.close(code=1011) # Internal Server Error
    finally:
        # This ensures disconnect is called even if an unhandled error occurs above
        # However, the current disconnect logic might try to remove it again if already removed.
        # For robustness, disconnect should handle being called on an already-removed websocket gracefully.
        # The manager's disconnect method should ideally be idempotent or check existence.
        # The provided manager code in prompt seems to handle this.
        print(f"Ensuring client #{client_id} is fully disconnected in finally block.")
        manager.disconnect(websocket, client_id) # Call disconnect here as a safeguard
