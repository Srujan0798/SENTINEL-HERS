# TASK — wave-10 / 05-voice-to-ticket-e2e

> Self-contained brief. Brownie feature (rubric: AI/Automation 20% + UI/UX 10%).

## Goal (one sentence)
Verify and harden the **voice-to-ticket** path end-to-end in the deployed app: speak → transcribe →
parse into a structured incident → it appears on the live dashboard, with a clean UX and graceful
handling when the browser mic or transcription is unavailable.

## Context
- Wave: 10. Depends on: wave-9 green + live deploy.
- Existing: `src/backend/voice/{transcribe,parse,routes}.py`, `src/frontend/src/components/voice/VoiceRecorder.tsx`, `tests/integration/test_voice.py`.

## Write-set (FM-13)
- `src/backend/voice/` (harden transcribe/parse; explicit errors)
- `src/frontend/src/components/voice/VoiceRecorder.tsx` (UX: recording state, permission-denied fallback, error surfacing)
- `tests/integration/test_voice.py` (extend — malformed audio + parse-failure branches)

## Forbid-set
- incidents model internals (consume its create API), auth, deploy config

## Blast radius
r1 (r2 if using a real speech API). Mic permission denial must degrade to a typed-input fallback, never a dead button.

## Steps
1. Trace the full path: audio → `transcribe` → `parse` → incident create. Confirm each step errors loudly on bad input (FM-11), not silent-empty.
2. UX: clear recording indicator; on mic-denied show a text fallback; on transcription failure show a real error, not a spinner forever.
3. Extend tests for the failure branches (empty/garbage audio, unparseable transcript).

## Acceptance (PROOF — FM-09)
- `python -m pytest tests/integration/test_voice.py -q` → pass (incl. new failure-branch tests). Paste it.
- Paste a sample transcript → parsed-incident JSON showing correct field extraction (title, severity, service).

## Guardrails
- FM-11 no silent failures on bad audio · FM-07 don't store raw audio with PII beyond need.

## Report to
`work/reports/wave-10/05-voice-to-ticket-e2e.report.md`
