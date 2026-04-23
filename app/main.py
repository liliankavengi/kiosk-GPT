"""
Kiosk-GPT — FastAPI Application Entrypoint.

WhatsApp-native kiosk management for Kenyan shopkeepers,
powered by AI (Llama 3.2) and Lightning Network (LDK Node).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.lightning import lightning_service
from app.utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs startup tasks before serving and cleanup tasks on shutdown.
    """
    settings = get_settings()
    logger.info(f"Starting Kiosk-GPT ({settings.app_env})")

    # Initialize Lightning service
    try:
        await lightning_service.initialize()
    except Exception as e:
        logger.warning(f"Lightning service init failed (non-fatal): {e}")

    logger.info("Kiosk-GPT is ready ⚡")

    yield  # App is running

    # Shutdown
    logger.info("Shutting down Kiosk-GPT...")
    await lightning_service.shutdown()
    logger.info("Goodbye!")


# ── Create FastAPI app ───────────────────────────────────
app = FastAPI(
    title="Kiosk-GPT",
    description="WhatsApp-native kiosk management — AI + Lightning",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS (for dashboard) ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────
from app.api.health import router as health_router
from app.api.webhooks import router as webhook_router
from app.api.flows import router as flows_router

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(flows_router)


@app.get("/")
async def root():
    """Root endpoint — basic info."""
    return {
        "service": "kiosk-gpt",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
