# WAVE-11 — Green + Ship (win path)

## Reality
Wave-10 agents delivered real features (chat, anomaly UI, containers, postmortem, voice, CI)
but left the suite RED: **18 failed** (isolation + contract drift). Uncommitted.

## Win order (no parallel on GREEN)

```
1. AGENT_GREEN   (serial, one agent only)  → full suite 0 failed
2. COMMIT        (orchestrator/human)      → one clean commit or few
3. HUMAN_DEPLOY  push + Render + Vercel
4. AGENT_F_URLS  paste real HTTPS into README
5. AGENT_DEMO    live smoke checklist (optional but wins judges)
6. SUBMIT        GitHub + writeup + live URL
```

## Do NOT
- Run 5 agents in parallel on tests again (that caused FM-13 pollution)
- Mark DONE without `python -m pytest -q` full suite green
- Invent live URLs
