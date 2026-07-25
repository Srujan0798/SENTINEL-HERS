#!/usr/bin/env bash
# ETERNITY verify_live contract for SENTINEL — fail-closed
set -euo pipefail
API="${API:-https://sentinel-api-clu9.onrender.com}"
FE="${FE:-https://sentinel-hers.vercel.app}"

fail() { echo "FAIL: $*" >&2; exit 1; }

echo "== healthz =="
code=$(curl -sS -m 45 -o /tmp/vz.json -w "%{http_code}" "$API/healthz" || true)
[[ "$code" == "200" ]] || fail "healthz $code"
grep -q ok /tmp/vz.json || fail "healthz body"

echo "== demo-status (no password) =="
code=$(curl -sS -m 45 -o /tmp/ds.json -w "%{http_code}" "$API/api/demo-status" || true)
[[ "$code" == "200" ]] || fail "demo-status $code"
if grep -qiE 'Sentinel2026|login_hint|password' /tmp/ds.json; then
  fail "demo-status must not expose password/login_hint"
fi

echo "== login =="
code=$(curl -sS -m 45 -o /tmp/login.json -w "%{http_code}" -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@sentinel.io","password":"Sentinel2026!"}' || true)
[[ "$code" == "200" ]] || fail "login $code"
TOKEN=$(python3 -c "import json;print(json.load(open('/tmp/login.json')).get('access_token',''))")
[[ -n "$TOKEN" ]] || fail "no token"

echo "== unauth deny =="
for path in /api/voice/incidents /api/health/services/ /api/incidents; do
  c=$(curl -sS -m 20 -o /dev/null -w "%{http_code}" -X GET "$API$path" 2>/dev/null || \
      curl -sS -m 20 -o /dev/null -w "%{http_code}" -X POST "$API$path" 2>/dev/null || echo 000)
  # accept 401/403/405/422 as not open data
  case "$c" in 401|403|405|422) ;; *) echo "warn $path $c" ;; esac
done
c=$(curl -sS -m 20 -o /dev/null -w "%{http_code}" -X POST "$API/api/voice/incidents")
[[ "$c" == "401" || "$c" == "403" ]] || fail "voice unauth expected 401 got $c"
c=$(curl -sS -m 20 -o /dev/null -w "%{http_code}" "$API/api/health/services/")
[[ "$c" == "401" || "$c" == "403" ]] || fail "health unauth expected 401 got $c"

echo "== auth core =="
c=$(curl -sS -m 40 -o /tmp/inc.json -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$API/api/incidents")
[[ "$c" == "200" ]] || fail "incidents $c"

echo "== FE login page =="
c=$(curl -sS -m 20 -o /dev/null -w "%{http_code}" "$FE/login" || true)
[[ "$c" == "200" || "$c" == "307" || "$c" == "308" ]] || fail "FE login $c"

echo "PASS verify_live SENTINEL"
exit 0
