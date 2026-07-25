#!/usr/bin/env bash
set -euo pipefail

# SENTINEL — Live production verification script (Phase 8)
# Run against the live deployment to validate the sacred demo path.
# Exits 0 on success, 1 on any failure.

BASE="${1:-https://sentinel-api-clu9.onrender.com}"
FAIL=0

red()   { printf "\033[31m✗ FAIL\033[0m %s\n" "$1"; }
green() { printf "\033[32m✓ OK\033[0m   %s\n" "$1"; }

# 1. Healthz
echo "=== 1. Healthz ==="
if curl -sf -m 10 "$BASE/healthz" > /dev/null 2>&1; then
  green "/healthz → 200"
else
  red "/healthz → not 200"
  FAIL=1
fi

# 2. Demo status — ready, open_sev1 ≥ 1, no password leak
echo "=== 2. Demo Status ==="
DEMO=$(curl -sf -m 10 "$BASE/api/demo-status" 2>/dev/null || echo "{}")
READY=$(echo "$DEMO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ready',False))" 2>/dev/null || echo "false")
SEV1=$(echo "$DEMO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('open_sev1_count',0))" 2>/dev/null || echo "0")
PASSWORD_LEAK=$(echo "$DEMO" | python3 -c "import sys,json; d=json.load(sys.stdin); print('password' in str(d) and 'hidden' not in str(d.get('login_hint','')))" 2>/dev/null || echo "true")
if [ "$READY" = "True" ]; then green "demo ready"; else red "demo not ready"; FAIL=1; fi
if [ "$SEV1" -ge 1 ]; then green "open_sev1_count=$SEV1"; else red "no open SEV1"; FAIL=1; fi
if [ "$PASSWORD_LEAK" = "False" ]; then green "no password leak"; else red "password leaked in demo-status"; FAIL=1; fi

# 3. Login → JWT
echo "=== 3. Login ==="
LOGIN_RESP=$(curl -sf -m 10 -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@sentinel.io","password":"Sentinel2026!"}' 2>/dev/null || echo "{}")
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -n "$TOKEN" ] && [ "$TOKEN" != "" ]; then
  green "JWT obtained"
else
  red "Login failed — no JWT"
  FAIL=1
fi

# 4. Unauth voice → 401
echo "=== 4. Unauth voice ==="
VOICE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -X POST "$BASE/api/voice/incidents" \
  -H "Content-Type: application/json" \
  -d '{"audio_b64":"","team_id":"test"}' 2>/dev/null || echo "000")
if [ "$VOICE_CODE" = "401" ]; then
  green "Unauth voice → 401"
else
  red "Unauth voice → $VOICE_CODE (expected 401)"
  FAIL=1
fi

# 5. Unauth health → 401
echo "=== 5. Unauth health ==="
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$BASE/api/health/services/" 2>/dev/null || echo "000")
if [ "$HEALTH_CODE" = "401" ]; then
  green "Unauth health → 401"
else
  red "Unauth health → $HEALTH_CODE (expected 401)"
  FAIL=1
fi

# 6. Incidents list
echo "=== 6. Incidents ==="
INCIDENTS=$(curl -sf -m 10 -H "Authorization: Bearer $TOKEN" "$BASE/api/incidents?per_page=1" 2>/dev/null || echo "{}")
TOTAL=$(echo "$INCIDENTS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pagination',{}).get('total',0))" 2>/dev/null || echo "0")
SEV1_ID=$(echo "$INCIDENTS" | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',[]); print(d[0]['id'] if d else '')" 2>/dev/null || echo "")
if [ "$TOTAL" -ge 1 ]; then green "incidents=$TOTAL"; else red "no incidents"; FAIL=1; fi
if [ -n "$SEV1_ID" ]; then green "SEV1 ID=$SEV1_ID"; else red "no SEV1 id"; FAIL=1; fi

# 7. AI summary — not mock
echo "=== 7. AI Summary ==="
SUMMARY=$(curl -sf -m 30 -H "Authorization: Bearer $TOKEN" "$BASE/api/ai/incidents/$SEV1_ID/summary" 2>/dev/null || echo "{}")
SUMMARY_LEN=$(echo "$SUMMARY" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('summary','')))" 2>/dev/null || echo "0")
IS_MOCK=$(echo "$SUMMARY" | python3 -c "import sys,json; print(int('mock-ai' in json.load(sys.stdin).get('summary','').lower()))" 2>/dev/null || echo "0")
if [ "$SUMMARY_LEN" -gt 80 ] && [ "$IS_MOCK" -eq 0 ]; then green "AI summary length=$SUMMARY_LEN (not mock)"; else red "AI summary too short or mock"; FAIL=1; fi

# 8. AI RCA — hypotheses
echo "=== 8. AI RCA ==="
RCA=$(curl -sf -m 30 -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "$BASE/api/ai/incidents/$SEV1_ID/root-causes" 2>/dev/null || echo "{}")
RCA_COUNT=$(echo "$RCA" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('root_causes',[])))" 2>/dev/null || echo "0")
if [ "$RCA_COUNT" -ge 1 ]; then green "RCA hypotheses=$RCA_COUNT"; else red "no RCA hypotheses"; FAIL=1; fi

# 9. Timeline, tasks, SLA, channels all 200
echo "=== 9. Sub-endpoints ==="
TIMELINE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Authorization: Bearer $TOKEN" "$BASE/api/incidents/$SEV1_ID/timeline" 2>/dev/null || echo "000")
if [ "$TIMELINE_CODE" = "200" ]; then green "Timeline 200"; else red "Timeline $TIMELINE_CODE"; FAIL=1; fi

TASKS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Authorization: Bearer $TOKEN" "$BASE/api/incidents/$SEV1_ID/tasks" 2>/dev/null || echo "000")
if [ "$TASKS_CODE" = "200" ]; then green "Tasks 200"; else red "Tasks $TASKS_CODE"; FAIL=1; fi

SLA_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Authorization: Bearer $TOKEN" "$BASE/api/sla" 2>/dev/null || echo "000")
if [ "$SLA_CODE" = "200" ]; then green "SLA 200"; else red "SLA $SLA_CODE"; FAIL=1; fi

HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Authorization: Bearer $TOKEN" "$BASE/api/health/services/" 2>/dev/null || echo "000")
if [ "$HEALTH_CODE" = "200" ]; then green "Health 200"; else red "Health $HEALTH_CODE"; FAIL=1; fi

# 10. SSE connected
echo "=== 10. SSE ==="
SSE_OUT=$(timeout 5 curl -s -N "$BASE/api/realtime/events?token=$TOKEN" 2>/dev/null || echo "")
SSE_OK=$(echo "$SSE_OUT" | head -1 | grep -c "event: connected" 2>/dev/null || echo "0")
if [ "$SSE_OK" -ge 1 ]; then green "SSE connected event"; else red "SSE no connected event"; FAIL=1; fi

# 11. Assign
echo "=== 11. Assign ==="
ASSIGN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE/api/incidents/$SEV1_ID/assign" \
  -d '{"user_id":"bd67b274-7dd2-4d63-b55c-6f5b1cae4670"}' 2>/dev/null || echo "000")
if [ "$ASSIGN_CODE" = "200" ]; then green "Assign 200"; else red "Assign $ASSIGN_CODE"; FAIL=1; fi

# 12. Escalate
echo "=== 12. Escalate ==="
ESC_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE/api/incidents/$SEV1_ID/escalate" \
  -d '{"user_id":"bd67b274-7dd2-4d63-b55c-6f5b1cae4670","reason":"Needs senior review"}' 2>/dev/null || echo "000")
if [ "$ESC_CODE" = "200" ]; then green "Escalate 200"; else red "Escalate $ESC_CODE"; FAIL=1; fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  printf "\033[32m=== ALL PASSED ===\033[0m\n"
  exit 0
else
  printf "\033[31m=== SOME FAILED ===\033[0m\n"
  exit 1
fi
