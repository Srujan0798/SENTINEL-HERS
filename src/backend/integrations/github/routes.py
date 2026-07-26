"""GitHub webhook ingestion + deployment/commit listing."""
import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.integrations.github.models import Commit, Deployment
from src.backend.shared_models import TeamModel

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _verify_github_sig(body: bytes, sig_header: str | None) -> None:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    is_prod = os.getenv("ENV", "development").lower() in ("production", "prod")
    if not secret:
        if is_prod:
            raise HTTPException(status_code=401, detail="GITHUB_WEBHOOK_SECRET not configured")
        return  # skip in dev/test
    if not sig_header or not sig_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing GitHub signature")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")


def _resolve_team(db: Session, team_id: str | None) -> str:
    """Resolve and validate the destination team for an incoming webhook.

    The team is taken from the `team_id` configured on the webhook URL and must
    correspond to a real team. We reject unknown teams rather than writing to a
    placeholder so deployments/commits are always correctly tenant-scoped.

    NOTE: the webhook secret is currently shared; binding a per-team secret at
    registration time is the next hardening step (see docs/SECURITY.md).
    """
    if not team_id:
        raise HTTPException(status_code=400, detail="team_id query parameter is required")
    team = db.query(TeamModel).filter(TeamModel.id == str(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Unknown team_id")
    return str(team.id)


@router.post("/github/webhook", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    team_id: str | None = Query(None, description="Destination team (set on the webhook URL)"),
    db: Session = Depends(get_db),
):
    body = await request.body()
    _verify_github_sig(body, x_hub_signature_256)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = x_github_event or ""
    team_id = _resolve_team(db, team_id)

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
            logger.warning("Failed to publish deployment realtime event")

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
    team_id: str | None = Query(None, description="Destination team (set on the webhook URL)"),
    db: Session = Depends(get_db),
):
    expected = os.getenv("GITLAB_WEBHOOK_SECRET", "")
    is_prod = os.getenv("ENV", "development").lower() in ("production", "prod")
    if not expected:
        if is_prod:
            raise HTTPException(status_code=401, detail="GITLAB_WEBHOOK_SECRET not configured")
    elif x_gitlab_token != expected:
        raise HTTPException(status_code=401, detail="Invalid GitLab token")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = x_gitlab_event or payload.get("object_kind", "")
    team_id = _resolve_team(db, team_id)

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

    elif event in ("merge_request", "Merge Request Hook"):
        attrs = payload.get("object_attributes", {})
        repo_name = payload.get("project", {}).get("name", "unknown")
        action = attrs.get("action", "open")
        source_branch = attrs.get("source_branch", "")
        target_branch = attrs.get("target_branch", "")
        mr_title = attrs.get("title", "")

        db.add(Commit(
            id=str(uuid.uuid4()),
            team_id=team_id,
            sha=attrs.get("last_commit", {}).get("id", ""),
            message=f"Merge Request !{attrs.get('iid', '')}: {mr_title} ({source_branch}→{target_branch})",
            author=payload.get("user", {}).get("name", ""),
            service=repo_name,
            branch=target_branch,
            source="gitlab",
            committed_at=datetime.utcnow(),
        ))
        db.commit()

        try:
            from src.backend.realtime.hub import get_hub
            import asyncio
            hub = get_hub()
            asyncio.create_task(hub.publish(team_id, "deployment.created", {
                "service": repo_name, "event": "merge_request", "action": action,
                "source_branch": source_branch, "target_branch": target_branch,
                "title": mr_title, "source": "gitlab",
            }))
        except Exception:
            logger.warning("Failed to publish MR realtime event")

    elif event in ("pipeline", "Pipeline Hook"):
        attrs = payload.get("object_attributes", {})
        repo_name = payload.get("project", {}).get("name", "unknown")
        pipeline_status = attrs.get("status", "pending")
        pipeline_ref = attrs.get("ref", "")
        pipeline_sha = attrs.get("sha", "")

        dep = Deployment(
            id=str(uuid.uuid4()),
            team_id=team_id,
            service=repo_name,
            environment="staging" if "staging" in pipeline_ref else "production",
            version=pipeline_ref.replace("refs/heads/", ""),
            sha=pipeline_sha,
            status=pipeline_status,
            source="gitlab",
            deployed_by="gitlab-ci",
            deployed_at=datetime.utcnow(),
            metadata_={"pipeline_id": str(attrs.get("id", "")), "ref": pipeline_ref},
        )
        db.add(dep)
        db.commit()

        try:
            from src.backend.realtime.hub import get_hub
            import asyncio
            hub = get_hub()
            asyncio.create_task(hub.publish(team_id, "deployment.created", {
                "id": dep.id, "service": dep.service, "status": dep.status,
                "source": "gitlab", "event": "pipeline",
            }))
        except Exception:
            logger.warning("Failed to publish pipeline realtime event")

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
