# Redis Multi-Worker SSE Setup

## How it works

`RealtimeHub` in `src/backend/realtime/hub.py` supports two modes:

### Mode 1: In-memory (default, single worker)
- All SSE clients connect to one process
- Events published directly to in-memory subscriber dicts
- No Redis dependency
- **Limitation:** Only works with single uvicorn worker

### Mode 2: Redis pub/sub (multi-worker)
- Set `REDIS_URL` env var (e.g. `redis://:password@host:6379/0`)
- Hub publishes events to Redis channel `team:<team_id>`
- All workers subscribe to their team's channel
- Events from any worker reach all connected clients across workers

## Deployment

### Single worker (current — Render free tier)
No Redis needed. The hub uses in-memory fan-out. SSE works within the single process.

### Multi-worker (scale)
```bash
# Set Redis URL
export REDIS_URL="redis://:password@your-redis-instance:6379/0"

# Start multiple workers
uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Each worker auto-detects `REDIS_URL` and switches to pub/sub mode.

## Verification
```bash
# With Redis configured, SSE events should appear from any worker
curl -N "https://your-api.com/api/realtime/events" -H "Authorization: Bearer $TOKEN"
# Create an incident via another worker → SSE event arrives
```

## Tested
- In-memory mode: integration tests
- Redis mode: local docker-compose with 2 uvicorn workers
