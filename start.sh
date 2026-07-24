#!/bin/bash
# SENTINEL — Render start script
# Uses ${PORT} from Render env with shell fallback to 10000.
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-10000}"
