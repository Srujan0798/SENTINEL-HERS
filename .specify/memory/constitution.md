# Constitution — SENTINEL

Immutable principles every wave/agent obeys.

1. **Dual-tier discipline.** Orchestrator plans + reviews; never writes feature code. Workers execute
   one task; never plan or expand scope.
2. **Contracts-first.** The wave-0 OpenAPI + schema are the single source of truth. Code to them.
3. **Disjoint writes (FM-13).** Parallel agents never share a write target.
4. **Evidence before "done" (FM-09).** Every report carries the acceptance command + its real output.
5. **Fail loud (FM-11).** No swallowed errors, no silent fallbacks, no synthetic data to fake a pass —
   this is incident tooling; hidden failures are the cardinal sin.
6. **One metric source (FM-05).** Numbers derive from Prometheus / `results/metrics.json`, never hand-typed.
7. **Realtime is a feature, not a bonus.** Watched state changes emit events.
8. **Protect the demo path.** The sacred end-to-end flow (SCOPE_GUARD.md) is defended before adding breadth.
9. **Never delete — archive.** Superseded work → `attic/` / `docs/historical/`.
10. **Secrets never committed (FM-07).** `.env` gitignored; rotate anything leaked.
