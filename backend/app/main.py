from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.observability.logging import setup_logging
from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.query import router as query_router

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.include_router(health_router, tags=["Health"])
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(query_router, tags=["RAG Query"])

@app.get("/")
async def root():
    return {"message": "Welcome to RAG Production API"}
