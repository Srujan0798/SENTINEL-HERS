You are a Tier-2 worker. Docs only. STOP after.

FRONTEND_URL = __PASTE_VERCEL_URL_HERE__
BACKEND_URL = __PASTE_RENDER_URL_HERE__

If still placeholders → BLOCKED.

Write-set ONLY:
- README.md
- docs/SUBMISSION.md
- work/reports/wave-11/03-url-polish.report.md

Put both live https URLs in README table. No invented metrics.

Acceptance:
grep -c "https://" README.md
grep -E "vercel|onrender" README.md

Then STOP.
