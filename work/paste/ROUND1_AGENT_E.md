You are a Tier-2 worker on SENTINEL (METIS Hard — AI-native engineering ops platform).
Execute ONE self-contained task and STOP. Do not plan other waves. Do not push or deploy.

# LAW
1. Build ONLY what this brief asks. Write ONLY to the write-set. Never touch the forbid-set.
2. Do NOT redesign architecture or expand scope.
3. Fail loud: bad audio / parse failure must error clearly — never silent empty success.
4. Run acceptance commands. Paste REAL terminal output in your report. No proof = not done.
5. Write report to the exact path below.
6. If blocked: report BLOCKED with one specific question — do not guess.
7. Sacred demo path must keep working.
8. Repo root: SENTINEL-HERS. Do not store raw audio with unnecessary PII. Do not commit secrets.

# TASK — wave-10 / 05-voice-to-ticket-e2e

## Goal (one sentence)
Verify and harden the **voice-to-ticket** path end-to-end: speak → transcribe → parse into a
structured incident → appears on dashboard, with clean UX when mic or transcription is unavailable.

## Context
- Existing: `src/backend/voice/{transcribe,parse,routes}.py`,
  `src/frontend/src/components/voice/VoiceRecorder.tsx`, `tests/integration/test_voice.py`.

## Write-set (ONLY these paths)
- `src/backend/voice/`
- `src/frontend/src/components/voice/VoiceRecorder.tsx`
- `tests/integration/test_voice.py` (extend — malformed audio + parse-failure branches)
- `work/reports/wave-10/05-voice-to-ticket-e2e.report.md`

## Forbid-set
- incidents model internals (consume create API only), auth, deploy config
- chat / anomaly / containers / postmortem files

## Blast radius
r1. Mic permission denial must degrade to typed-input fallback — never a dead button.

## Steps
1. Trace: audio → transcribe → parse → incident create. Each step errors loud on bad input.
2. UX: recording indicator; mic-denied → text fallback; transcription failure → real error (not infinite spinner).
3. Extend tests: empty/garbage audio, unparseable transcript.

## Acceptance (PROOF required)
- `python -m pytest tests/integration/test_voice.py -q` → pass (incl. new failure branches). Paste output.
- Paste sample transcript → parsed-incident JSON (title, severity, service).

## Report path
`work/reports/wave-10/05-voice-to-ticket-e2e.report.md`

### Report template
```
# REPORT — wave-10 / 05-voice-to-ticket-e2e
- **Agent:** <name>
- **Result:** DONE | PARTIAL | BLOCKED
- **Date:** <YYYY-MM-DD>
## What I changed
## Acceptance proof (REQUIRED)
```
$ command
output
```
## Deviations
## Gotchas
## Follow-ups
```

Then STOP.
