"""FastAPI application entrypoint with lifespan management."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db import neo4j_client, postgres, qdrant_client, redis_client
from src.routes.agents import router as agents_router
from src.routes.auth import router as auth_router
from src.routes.avatar import router as avatar_router
from src.routes.conversations import router as conversations_router
from src.routes.evolution import router as evolution_router
from src.routes.graph import router as graph_router
from src.routes.insights import router as insights_router
from src.routes.onboarding import router as onboarding_router
from src.routes.permissions import router as permissions_router
from src.routes.scheduler import router as scheduler_router
from src.routes.teachback import router as teachback_router
from src.routes.verification import router as verification_router
from src.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Connect all databases on startup, disconnect on shutdown."""
    setup_logging()
    logger.info("starting_nexusmind", env=settings.app.env)

    # Connect all databases in parallel
    await asyncio.gather(
        postgres.connect(),
        neo4j_client.connect(),
        qdrant_client.connect(),
        redis_client.connect(),
    )
    logger.info("all_databases_connected")

    yield

    # Disconnect all databases in parallel
    await asyncio.gather(
        postgres.disconnect(),
        neo4j_client.disconnect(),
        qdrant_client.disconnect(),
        redis_client.disconnect(),
    )
    logger.info("all_databases_disconnected")


app = FastAPI(
    title="NexusMind",
    description="Self-learning collective intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(agents_router)
app.include_router(permissions_router)
app.include_router(graph_router)
app.include_router(conversations_router)
app.include_router(insights_router)
app.include_router(verification_router)
app.include_router(teachback_router)
app.include_router(avatar_router)
app.include_router(scheduler_router)
app.include_router(evolution_router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
