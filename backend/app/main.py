"""
FastAPI application entry-point.
"""

import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    await init_db()

    # ── Start email ingestion if configured ──────────────
    import asyncio
    from app.config import settings as cfg
    from app.services.email_ingestion import init_email_service

    if cfg.EMAIL_ADDRESS and cfg.EMAIL_PASSWORD:
        svc = init_email_service(
            imap_server=cfg.EMAIL_IMAP_SERVER,
            email_address=cfg.EMAIL_ADDRESS,
            password=cfg.EMAIL_PASSWORD,
        )
        asyncio.create_task(svc.start())
        logger.info("📧 Email ingestion started for %s", cfg.EMAIL_ADDRESS)
    else:
        logger.info("📧 Email ingestion not configured (EMAIL_ADDRESS/EMAIL_PASSWORD missing)")

    yield


app = FastAPI(
    title="HireAI",
    description="HireAI — AI-powered recruitment platform.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler so 500 errors return useful info in dev mode."""
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────
from app.routers.auth_router import router as auth_router          # noqa: E402
from app.routers.candidate_router import router as candidate_router  # noqa: E402
from app.routers.ingestion_router import router as ingestion_router  # noqa: E402
from app.routers.search_router import router as search_router        # noqa: E402
from app.routers.job_router import router as job_router              # noqa: E402
from app.routers.application_router import router as application_router  # noqa: E402
from app.routers.ai_router import router as ai_router                # noqa: E402
from app.routers.dedupe_router import router as dedupe_router        # noqa: E402
from app.routers.ml_router import router as ml_router                # noqa: E402
from app.routers.chatbot_router import router as chatbot_router      # noqa: E402

app.include_router(auth_router)
app.include_router(candidate_router)
app.include_router(ingestion_router)
app.include_router(search_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(ai_router)
app.include_router(dedupe_router)
app.include_router(ml_router)
app.include_router(chatbot_router)


@app.get("/", tags=["health"])
async def health_check():
    """Root health-check endpoint."""
    return {"status": "ok", "service": "HireAI"}
