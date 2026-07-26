import asyncio as _asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.backend.rate_limit import limiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Background task definitions (defined before lifespan so they can be started)
# --------------------------------------------------------------------------- #

async def _cleanup_expired_tokens():
    """Purge expired RevokedToken rows every 6 hours."""
    while True:
        try:
            from src.backend.db import SessionLocal
            from src.backend.shared_models import RevokedToken
            db = SessionLocal()
            try:
                cut = datetime.now(timezone.utc)
                deleted = db.query(RevokedToken).filter(RevokedToken.expires_at < cut).delete()
                if deleted:
                    db.commit()
                    logger.info("Cleaned %d expired revoked tokens", deleted)
            finally:
                db.close()
        except Exception as e:
            logger.warning("Token cleanup failed: %s", e)
        await _asyncio.sleep(21600)


async def _background_embed_loop():
    """Catch up on unembedded logs every 30 minutes."""
    await _asyncio.sleep(120)  # wait for app to settle
    while True:
        try:
            from src.backend.db import SessionLocal
            from src.backend.ai.embeddings import embed_recent_logs
            from src.backend.shared_models import TeamModel
            db = SessionLocal()
            try:
                teams = db.query(TeamModel).all()
                for team in teams:
                    try:
                        n = embed_recent_logs(db, str(team.id), limit=50)
                        if n:
                            logger.info("Embedded %d logs for team %s", n, team.id)
                    except Exception as team_err:
                        logger.warning("Embedding for team %s failed: %s", team.id, team_err)
            finally:
                db.close()
        except Exception as e:
            logger.warning("Background embedding failed: %s", e)
        await _asyncio.sleep(1800)


async def _health_prober_loop():
    """Run health probing if enabled."""
    from src.backend.health.prober import start_health_prober
    await start_health_prober()


# --------------------------------------------------------------------------- #
# Lifecycle manager
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks once the event loop is running; cancel on shutdown."""
    tasks = [_asyncio.create_task(_cleanup_expired_tokens()), _asyncio.create_task(_background_embed_loop())]
    if os.getenv("ENABLE_HEALTH_PROBER", "0").lower() in ("1", "true", "yes"):
        tasks.append(_asyncio.create_task(_health_prober_loop()))
    logger.info("Background tasks started: cleanup, embedding%s", ", health" if len(tasks) > 2 else "")
    yield
    for t in tasks:
        t.cancel()
    await _asyncio.gather(*tasks, return_exceptions=True)


# --------------------------------------------------------------------------- #
# App construction
# --------------------------------------------------------------------------- #

app = FastAPI(title="SENTINEL API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Production AI check: fail boot if AI_PROVIDER is mock or keys missing (unless ALLOW_MOCK_AI=1)
_is_prod = os.getenv("ENV", "development").lower() in ("production", "prod")
if _is_prod:
    _ai_provider = os.getenv("AI_PROVIDER", "mock").lower()
    _allow_mock = os.getenv("ALLOW_MOCK_AI", "0").lower() in ("1", "true", "yes")
    if _ai_provider == "mock" and not _allow_mock:
        logger.error("AI_PROVIDER=mock in production. Set a real provider or ALLOW_MOCK_AI=1 for emergency.")
        sys.exit(1)
    _key_map = {"claude": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY", "nvidia": "NVAPI_KEY"}
    _needed_key = _key_map.get(_ai_provider)
    if _needed_key and not os.getenv(_needed_key):
        logger.error("AI_PROVIDER=%s but %s is not set in production.", _ai_provider, _needed_key)
        sys.exit(1)

# Run DB migrations + optional demo auto-seed before handling any request
try:
    from api.startup import run_migrations
    run_migrations()
except Exception as _e:
    logger.warning("DB migration/auto-seed skipped: %s", _e)

# CORS allow-list from env (comma-separated). Falls back to localhost dev origins
# when CORS_ORIGINS is unset so dev + tests are unchanged. Explicit allow-list only —
# never "*" with credentials.
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://sentinel-hers.vercel.app",
    "https://sentinel-hers-git-main-srujan-sais-projects.vercel.app",
]
_cors_env = os.getenv("CORS_ORIGINS")
if _cors_env:
    cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    cors_origins = list(_DEFAULT_CORS_ORIGINS)
if not cors_origins:
    cors_origins = list(_DEFAULT_CORS_ORIGINS)
logger.info("CORS allow-list: %s", cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.backend.metrics import metrics_middleware, metrics_endpoint
app.middleware("http")(metrics_middleware)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return metrics_endpoint()


from src.backend.auth.routes import router as auth_router
app.include_router(auth_router)

from src.backend.health.routes import router as health_router
app.include_router(health_router)

from src.backend.ingest.routes import router as ingest_router
app.include_router(ingest_router)

from src.backend.logs.routes import router as logs_router
app.include_router(logs_router)

from src.backend.incidents.routes import router as incidents_router
app.include_router(incidents_router)

from src.backend.ai.routes import router as ai_router
app.include_router(ai_router)

from src.backend.integrations.github.routes import router as integrations_router
app.include_router(integrations_router)

from src.backend.tasks.routes import router as tasks_router
app.include_router(tasks_router)

# Comms router must be imported AFTER incidents so the auto-channel lifecycle
# hook is installed before the first incident is created. Importing this package
# patches IncidentService.create_incident.
from src.backend.comms import comms_router  # noqa: E402  — installs lifecycle hook
app.include_router(comms_router)

from src.backend.analytics.routes import router as analytics_router
app.include_router(analytics_router)

from src.backend.ml.anomaly.routes import router as ml_router
app.include_router(ml_router)

from src.backend.integrations.containers.routes import router as containers_router
app.include_router(containers_router)

from src.backend.voice.routes import router as voice_router
app.include_router(voice_router)

from src.backend.seed.routes import router as seed_router
app.include_router(seed_router)

# Realtime SSE + WebSocket (StatusBar / Comms live updates)
from src.backend.realtime.router import router as realtime_router
app.include_router(realtime_router, prefix="/api")
