#!/usr/bin/env bash
# Keep Render free tier warm — ping healthz every 5 minutes.
# Usage: cron */5 * * * * /path/to/keep_alive.sh
# Or: launchctl on macOS, or Render Cron Job, or UptimeRobot external ping.
set -euo pipefail
URL="${1:-https://sentinel-api-clu9.onrender.com/healthz}"
curl -sf -m 30 "$URL" > /dev/null 2>&1 && echo "$(date): warm" || echo "$(date): failed"