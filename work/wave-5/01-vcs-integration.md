# TASK — wave-5 / 01-vcs-integration

## Goal
GitHub + GitLab webhook ingestion: link deploys and commits to incidents. Deployment tracking.

## Context
- Wave: 5. Depends on wave-2 (incidents). Schema: `deployments`, `commits` tables.
- Blast radius r3 (outbound: webhook validation uses external secrets). Tokens in env: `GITHUB_WEBHOOK_SECRET`, `GITLAB_WEBHOOK_SECRET`.

## Write-set (ONLY these)
- src/backend/integrations/github/
- src/backend/integrations/gitlab/

## Forbid-set
- src/backend/timeline/ (02 owns), all frontend/**, all other backend/

## Blast radius
r1 for code; r3 for live webhook testing (need valid token). Use test mode (signature replay) for acceptance.

## Steps
1. `POST /api/integrations/github/webhook` — validates HMAC-SHA256 signature, handles events:
   - `deployment` / `deployment_status` → create/update `Deployment` record.
   - `push` → create `Commit` records; link to deployment if sha matches.
   - `release` → tag as deployment event.
2. `POST /api/integrations/gitlab/webhook` — validates `X-Gitlab-Token`, handles same event types.
3. Both: on new deployment/commit → emit `deployment.created` to realtime hub + link to open incidents (matching service name).
4. `GET /api/integrations/deployments` — list deployments with commit SHAs + status.
5. `GET /api/integrations/commits` — list recent commits per service.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_vcs_integration.py -v
# Replays captured webhook payloads with valid test signatures.
# Expected: deployment created, commit linked, realtime event emitted
```

## Report to
`work/reports/wave-5/01-vcs-integration.report.md`
