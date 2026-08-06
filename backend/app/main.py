from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.api.routes.upload import router as upload_router
from app.api.routes.workspaces import router as workspaces_router
from app.config import settings
from app.observability.logging import setup_logging
from app.progress import hub

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["Health"])
app.include_router(upload_router, tags=["Upload"])
app.include_router(workspaces_router, tags=["Workspaces"])
app.include_router(query_router, tags=["RAG Query"])


@app.websocket("/ws/progress/{channel}")
async def progress_socket(websocket: WebSocket, channel: str):
    """Live pipeline stage events for one upload/query channel."""
    await hub.connect(channel, websocket)
    try:
        while True:
            # No inbound protocol; this just keeps the socket open and
            # notices when the client goes away.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(channel, websocket)
    except Exception:
        await hub.disconnect(channel, websocket)


@app.get("/")
async def root():
    return {"message": "Welcome to RAG Production API"}
