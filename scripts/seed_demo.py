#!/usr/bin/env python3
"""Seed SENTINEL with realistic demo data for the hackathon demo path."""
import os
import sys
import datetime
import json
import requests

BASE_URL = os.getenv("SENTINEL_URL", "http://localhost:8000")


def post(path, data, token=None, params=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(f"{BASE_URL}{path}", json=data, headers=headers, params=params)
    if r.status_code not in (200, 201):
        print(f"  WARN {path} → {r.status_code}: {r.text[:200]}")
        return None
    return r.json()


def get(path, token=None, params=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"{BASE_URL}{path}", headers=headers, params=params)
    return r.json() if r.ok else None


def main():
    print("=== SENTINEL Demo Seed ===")

    # 1. Register demo user
    print("\n[1] Registering demo user…")
    user = post("/auth/register", {
        "email": "demo@sentinel.io",
        "password": "Sentinel2026!",
        "name": "Demo User",
        "team_name": "Acme SRE",
    })
    if not user:
        print("  Already registered — logging in…")
        user = post("/auth/login", {"email": "demo@sentinel.io", "password": "Sentinel2026!"})
    if not user:
        print("ERROR: Could not register or login."); sys.exit(1)
    token = user["access_token"]
    team_id = user["user"]["team_id"]
    print(f"  token acquired: {token[:30]}…")
    print(f"  team_id: {team_id}")

    # 2. Ingest logs
    print("\n[2] Ingesting sample logs…")
    now = datetime.datetime.now(datetime.UTC)
    log_entries = [
        {"service": "api-gateway", "level": "error", "message": "Database connection pool exhausted after 30s", "timestamp": (now - datetime.timedelta(minutes=30)).isoformat(), "metadata": {"host": "prod-node-01", "env": "production"}},
        {"service": "payments", "level": "error", "message": "Payment service timeout: upstream response > 5000ms", "timestamp": (now - datetime.timedelta(minutes=25)).isoformat(), "metadata": {"host": "prod-node-02", "env": "production"}},
        {"service": "redis-cache", "level": "warn", "message": "Redis cache miss rate spike: 94% miss ratio", "timestamp": (now - datetime.timedelta(minutes=20)).isoformat(), "metadata": {"host": "prod-node-03", "env": "production"}},
        {"service": "api-gateway", "level": "info", "message": "API gateway latency p99 > 2000ms", "timestamp": (now - datetime.timedelta(minutes=15)).isoformat(), "metadata": {"host": "prod-node-04", "env": "production"}},
        {"service": "auth", "level": "error", "message": "Auth service: JWT validation failed for 1234 requests", "timestamp": (now - datetime.timedelta(minutes=10)).isoformat(), "metadata": {"host": "prod-node-05", "env": "production"}},
        {"service": "payments-worker", "level": "fatal", "message": "CRITICAL: Pod crash-loop detected in payments-worker", "timestamp": (now - datetime.timedelta(minutes=5)).isoformat(), "metadata": {"host": "prod-node-06", "env": "production"}},
    ]
    post("/api/ingest/logs", {"entries": log_entries}, token)
    print(f"  {len(log_entries)} log entries ingested")

    # 3. Create incidents
    print("\n[3] Creating incidents…")
    inc1 = post("/api/incidents", {
        "title": "Payment service cascade failure",
        "description": "Payment service is returning 503s due to database connection pool exhaustion. Error rate at 78%, p99 latency > 5s. Revenue impact estimated at $12k/min.",
        "severity": "SEV1",
    }, token, params={"team_id": team_id})
    inc2 = post("/api/incidents", {
        "title": "Redis cache miss rate spike",
        "description": "Cache miss ratio jumped from 5% to 94% after last deployment. Causing increased database load across all services.",
        "severity": "SEV2",
    }, token, params={"team_id": team_id})
    inc3 = post("/api/incidents", {
        "title": "Auth service elevated error rate",
        "description": "JWT validation failures spiking. 1234 failed auth requests in last 15 minutes.",
        "severity": "SEV3",
    }, token, params={"team_id": team_id})
    incidents = [x for x in [inc1, inc2, inc3] if x]
    print(f"  {len(incidents)} incidents created")

    if not incidents:
        print("ERROR: No incidents created"); sys.exit(1)

    inc_id = incidents[0]["id"]

    # 4. Ingest alerts
    print("\n[4] Ingesting alerts…")
    alerts = [
        {"source": "prometheus", "alert_type": "HighErrorRate", "title": "Error rate > 50% for payments service", "description": "Error rate > 50% for payments service", "severity": "critical", "metadata": {"service": "payments"}},
        {"source": "kubernetes", "alert_type": "PodCrashLoop", "title": "payments-worker crash-looping (8 restarts)", "description": "payments-worker crash-looping (8 restarts)", "severity": "critical", "metadata": {"service": "payments-worker"}},
        {"source": "datadog", "alert_type": "HighLatency", "title": "p99 API latency > 2s", "description": "p99 API latency > 2s", "severity": "warning", "metadata": {"service": "api-gateway"}},
    ]
    for alert in alerts:
        post("/api/ingest/alerts", alert, token)
    print(f"  {len(alerts)} alerts ingested")

    # 5. Add timeline events
    print("\n[5] Adding timeline events to SEV1 incident…")
    events = [
        {"type": "detection", "description": "PagerDuty alert fired: payment error rate > 50%"},
        {"type": "acknowledgement", "description": "On-call engineer paged and acknowledged"},
        {"type": "investigation", "description": "Root cause narrowed to DB connection pool exhaustion after cache flush"},
        {"type": "mitigation", "description": "Connection pool size increased from 10 → 50; error rate dropping"},
    ]
    for ev in events:
        post(f"/api/incidents/{inc_id}/timeline", ev, token, params={"actor": "system"})
    print(f"  {len(events)} timeline events added")

    # 6. Create tasks
    print("\n[6] Creating remediation tasks…")
    tasks = [
        {"title": "Increase DB connection pool size in prod", "priority": "high"},
        {"title": "Add circuit breaker to payments → DB calls", "priority": "high"},
        {"title": "Set up Redis eviction alerts", "priority": "medium"},
        {"title": "Update runbook for cache-flush incidents", "priority": "low"},
    ]
    for task in tasks:
        post(f"/api/incidents/{inc_id}/tasks", task, token)
    print(f"  {len(tasks)} tasks created")

    # 7. Score anomalies
    print("\n[7] Seeding anomaly scores…")
    metrics_stream = [
        {"service": "payments", "metrics": [0.92]},
        {"service": "api-gateway", "metrics": [0.85]},
        {"service": "redis-cache", "metrics": [0.97]},
        {"service": "auth", "metrics": [0.35]},
        {"service": "notifications", "metrics": [0.28]},
    ]
    for m in metrics_stream:
        result = post("/api/ml/score", m, token)
        if result:
            flag = "🚨 ANOMALY" if result.get("is_anomaly") else "✅ normal"
            print(f"    {m['service']}: score={result.get('score', 0):.3f} {flag}")

    # 8. Summary
    print("\n=== Seed Complete ===")
    print(f"  Base URL:   {BASE_URL}")
    print(f"  Email:      demo@sentinel.io")
    print(f"  Password:   Sentinel2026!")
    print(f"  Incidents:  {len(incidents)}")
    print(f"  Active SEV1 incident ID: {inc_id}")
    print()
    print("Demo path:")
    print("  1. Login at /login")
    print("  2. View incidents dashboard → click SEV1")
    print("  3. GET /api/ai/incidents/{id}/summary")
    print("  4. POST /api/ai/incidents/{id}/root-causes")
    print("  5. POST /api/ai/incidents/{id}/postmortem")
    print("  6. View anomaly dashboard /api/ml/anomalies")


if __name__ == "__main__":
    main()