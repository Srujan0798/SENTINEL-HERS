"""GitHub webhook ingestion + deployment/commit listing."""
import hashlib
import hmac
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.integrations.github.models import Commit, Deployment

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

_PLACEHOLDER_TEAM = "00000000-0000-0000-0000-000000000001"


def _verify_github_sig(body: bytes, sig_header: str | None) -> None:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return  # skip in dev/test
    if not sig_header or not sig_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing GitHub signature")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")


@router.post("/github/webhook", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    db: Session = Depends(get_db),
):
    body = await request.body()
    _verify_github_sig(body, x_hub_signature_256)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = x_github_event or ""
    team_id = _PLACEHOLDER_TEAM

    if event in ("deployment", "deployment_status"):
        dep_data = payload.get("deployment", payload.get("deployment_status", {}))
        dep = Deployment(
            id=str(uuid.uuid4()),
            team_id=team_id,
            service=payload.get("repository", {}).get("name", "unknown"),
            environment=dep_data.get("environment", "production"),
            version=dep_data.get("ref", ""),
            sha=dep_data.get("sha", ""),
            status=dep_data.get("state", "pending"),
            source="github",
            deployed_by=payload.get("sender", {}).get("login", ""),
            deployed_at=datetime.utcnow(),
            metadata_={"payload": str(payload)[:500]},
        )
        db.add(dep)
        db.commit()

        try:
            from src.backend.realtime.hub import get_hub
            import asyncio
            hub = get_hub()
            asyncio.create_task(hub.publish(team_id, "deployment.created", {
                "id": dep.id, "service": dep.service, "status": dep.status
            }))
        except Exception:
            pass

    elif event == "push":
        repo_name = payload.get("repository", {}).get("name", "unknown")
        for commit_data in payload.get("commits", [])[:20]:
            c = Commit(
                id=str(uuid.uuid4()),
                team_id=team_id,
                sha=commit_data.get("id", ""),
                message=commit_data.get("message", ""),
                author=commit_data.get("author", {}).get("name", ""),
                service=repo_name,
                branch=payload.get("ref", "").replace("refs/heads/", ""),
                source="github",
                committed_at=datetime.utcnow(),
            )
            db.add(c)
        db.commit()

    return {"status": "accepted", "event": event}


@router.post("/gitlab/webhook", status_code=status.HTTP_202_ACCEPTED)
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(None),
    x_gitlab_event: str | None = Header(None),
    db: Session = Depends(get_db),
):
    expected = os.getenv("GITLAB_WEBHOOK_SECRET", "")
    if expected and x_gitlab_token != expected:
        raise HTTPException(status_code=401, detail="Invalid GitLab token")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = x_gitlab_event or payload.get("object_kind", "")
    team_id = _PLACEHOLDER_TEAM

    if event in ("deployment", "Deployment Hook"):
        dep = Deployment(
            id=str(uuid.uuid4()),
            team_id=team_id,
            service=payload.get("project", {}).get("name", "unknown"),
            environment=payload.get("environment", "production"),
            sha=payload.get("sha", ""),
            status=payload.get("status", "pending"),
            source="gitlab",
            deployed_at=datetime.utcnow(),
        )
        db.add(dep)
        db.commit()

    elif event in ("push", "Push Hook"):
        repo_name = payload.get("project", {}).get("name", "unknown")
        for commit_data in payload.get("commits", [])[:20]:
            c = Commit(
                id=str(uuid.uuid4()),
                team_id=team_id,
                sha=commit_data.get("id", ""),
                message=commit_data.get("message", ""),
                author=commit_data.get("author", {}).get("name", ""),
                service=repo_name,
                branch=payload.get("ref", "").replace("refs/heads/", ""),
                source="gitlab",
                committed_at=datetime.utcnow(),
            )
            db.add(c)
        db.commit()

    return {"status": "accepted", "event": event}


@router.get("/deployments")
async def list_deployments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    rows = db.query(Deployment).filter(Deployment.team_id == team_id).order_by(
        Deployment.created_at.desc()
    ).limit(100).all()
    return [
        {
            "id": r.id, "service": r.service, "environment": r.environment,
            "version": r.version, "sha": r.sha, "status": r.status,
            "source": r.source, "deployed_by": r.deployed_by,
            "deployed_at": str(r.deployed_at) if r.deployed_at else None,
        }
        for r in rows
    ]


@router.get("/commits")
async def list_commits(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    rows = db.query(Commit).filter(Commit.team_id == team_id).order_by(
        Commit.created_at.desc()
    ).limit(100).all()
    return [
        {
            "id": r.id, "sha": r.sha, "message": r.message,
            "author": r.author, "service": r.service, "branch": r.branch,
            "source": r.source,
        }
        for r in rows
    ]
