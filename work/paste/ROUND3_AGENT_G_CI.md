You are a Tier-2 worker on SENTINEL. Execute ONE CI task and STOP. No product features.

# LAW
1. Write ONLY to the write-set.
2. No secrets in workflow. No deploy keys.
3. Fail loud on red tests/builds.
4. Paste proof that the workflow file is valid YAML and documents commands.

# TASK — CI shield (anti false-green)

## Goal
Add GitHub Actions so a missing package or red suite fails the build on every PR/push (prevents the logs-module regression forever).

## Write-set ONLY
- `.github/workflows/ci.yml`
- `work/reports/wave-10/07-ci-shield.report.md`

## Forbid-set
Application code, deploy configs, secrets.

## Required workflow behavior
On `push` and `pull_request` to `main`:

**Job backend:**
- checkout
- setup-python 3.11 or 3.12
- `pip install -r api/requirements.txt`
- `python -m pytest -q`
- env: `AI_PROVIDER=mock` (and any minimal JWT secrets as dummy test values if required)

**Job frontend:**
- checkout
- setup-node 20
- `cd src/frontend && npm ci`
- `NEXT_PUBLIC_API_BASE_URL=https://example.test npm run build`

## Acceptance
- File exists at `.github/workflows/ci.yml`
- Paste `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` or equivalent validation if PyYAML available; else paste file head + confirm two jobs.
- Do not claim CI ran on GitHub unless you saw it; local file creation is enough for DONE.

## Report path
`work/reports/wave-10/07-ci-shield.report.md`

Then STOP.
