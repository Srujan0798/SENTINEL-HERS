You are a Tier-2 worker on SENTINEL. Run ONLY if suite is already green but security review finds gaps. STOP after.

# TASK — security prove for judges (Security 15%)

## Write-set
- tests/integration/test_security_tenant.py (new)
- surgical src/backend/** only if a real hole found
- work/reports/wave-11/02-security-prove.report.md

## Prove with tests (mock)
1. Team A cannot read team B incidents/logs/chat/postmortem.
2. Unauthenticated GET on /api/integrations/deployments, /api/analytics/*, /api/ai/* → 401/403.
3. No webhook token leakage in responses (headers/body).

## Acceptance
python -m pytest tests/integration/test_security_tenant.py -q
Full suite still 0 failed: python -m pytest -q

Then STOP.
