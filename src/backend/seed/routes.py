import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.incidents.models import Incident
from src.backend.seed.service import DEMO_EMAIL, ensure_demo_seed
from src.backend.shared_models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["seed"])


@router.get("/demo-status")
async def demo_status(db: Session = Depends(get_db)):
    """Public readiness check for the judge demo path (no secrets)."""
    user = db.query(UserModel).filter(UserModel.email == DEMO_EMAIL).first()
    if not user:
        return {
            "ready": False,
            "demo_email": DEMO_EMAIL,
            "reason": "demo user missing — waiting for AUTO_SEED_DEMO or POST /api/seed",
        }
    team_id = str(user.team_id) if user.team_id else None
    incidents = (
        db.query(Incident).filter(Incident.team_id == team_id).count() if team_id else 0
    )
    sev1 = (
        db.query(Incident)
        .filter(Incident.team_id == team_id, Incident.severity == "SEV1")
        .count()
        if team_id
        else 0
    )
    open_sev1 = (
        db.query(Incident)
        .filter(
            Incident.team_id == team_id,
            Incident.severity == "SEV1",
            Incident.status.in_(("detected", "triaging", "investigating", "mitigating")),
        )
        .count()
        if team_id
        else 0
    )
    resolved = (
        db.query(Incident)
        .filter(Incident.team_id == team_id, Incident.resolved_at.isnot(None))
        .count()
        if team_id
        else 0
    )
    # Ready only when an *open* SEV1 exists for the sacred war-room demo path.
    ready = bool(user and incidents >= 1 and open_sev1 >= 1)
    # Never put the demo password in a public API body (judges use README / login UI).
    # ENV=production|prod OR common PaaS markers ⇒ treat as prod for any residual hints.
    env = os.getenv("ENV", "development").lower()
    is_prod = env in ("production", "prod") or bool(
        os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("RAILWAY_ENVIRONMENT")
    )
    body: dict = {
        "ready": ready,
        "demo_email": DEMO_EMAIL,
        "incident_count": incidents,
        "sev1_count": sev1,
        "open_sev1_count": open_sev1,
        "resolved_count": resolved,
        "frontend": "https://sentinel-hers.vercel.app",
        # Email only — password never returned (security + ETERNITY S7).
        "demo_login_path": "/login",
    }
    if not ready:
        body["reason"] = "no open SEV1 — run AUTO_SEED_DEMO repair or POST /api/seed"
    if not is_prod:
        body["hint"] = "Use README demo credentials on the login page (password not exposed via API)."
    return body


def _seed_secret() -> str | None:
    """Require explicit SEED_SECRET in env for HTTP seeding (no weak default in prod)."""
    return os.getenv("SEED_SECRET") or None


@router.post("/seed", status_code=201)
async def seed_demo(
    x_seed_secret: str | None = Header(None),
    x_ai_provider: str | None = Header(None),
    x_openrouter_key: str | None = Header(None),
    x_nvapi_key: str | None = Header(None),
    db: Session = Depends(get_db),
):
    secret = _seed_secret()
    # Allow default only when explicitly in non-production (local/dev).
    if not secret:
        if os.getenv("ENV", "development").lower() in ("production", "prod"):
            raise HTTPException(
                status_code=503,
                detail="SEED_SECRET not configured on server",
            )
        secret = "sentinel-seed-dev-only"

    if not x_seed_secret or x_seed_secret != secret:
        raise HTTPException(status_code=403, detail="Invalid seed secret")

    if x_ai_provider:
        os.environ["AI_PROVIDER"] = x_ai_provider
    if x_openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = x_openrouter_key
    if x_nvapi_key:
        os.environ["NVAPI_KEY"] = x_nvapi_key

    try:
        return ensure_demo_seed(db)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Seed failed")
        raise HTTPException(status_code=500, detail=f"Seed error: {e}") from e
