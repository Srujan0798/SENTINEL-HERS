import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SENTINEL API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

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
