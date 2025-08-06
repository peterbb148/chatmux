import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.models.message import Message
from app.services.connection_manager import ConnectionManager
from app.services.llm_coordinator import LLMCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatmux API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize connection manager and LLM coordinator
manager = ConnectionManager()
llm_coordinator = LLMCoordinator()


@app.get("/")
async def root():
    return {"message": "Chatmux API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/models")
async def get_models():
    """Get the configured models"""
    return {
        "models": [
            {"id": model_id, **info} for model_id, info in llm_coordinator.model_info.items()
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Parse the message
            message = Message(
                content=message_data["content"],
                targets=message_data.get("targets", []),
                user_id=message_data.get("user_id", "default"),
            )

            logger.info(f"Received message: {message.content}, targets: {message.targets}")

            # Send to LLM coordinator for processing
            await llm_coordinator.process_message(message, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
