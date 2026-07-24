# HUMAN ONLY — Deploy gate (not for OpenCode)

Do this yourself. Agents cannot complete submission without live URLs.

## Steps

```bash
cd /Users/srujansai/Desktop/SENTINEL-HERS
git status          # should show main ahead of origin
git push origin main
```

1. **Render** → New → Blueprint → connect this GitHub repo → Apply `render.yaml`
2. Render dashboard env for `sentinel-api`:
   - `ANTHROPIC_API_KEY` = your key
   - optional `GEMINI_API_KEY`
   - `CORS_ORIGINS` = temporary or wait for Vercel URL
3. Wait for deploy. Check:
   ```bash
   curl -sS https://<your-api>.onrender.com/healthz
   # expect: {"status":"ok"}
   ```
4. **Vercel** → New Project → same repo  
   - **Root Directory = `src/frontend`**  
   - Env: `NEXT_PUBLIC_API_BASE_URL=https://<your-api>.onrender.com` (no trailing slash)
5. Deploy. Note `https://<app>.vercel.app`
6. Back to Render: set `CORS_ORIGINS=https://<app>.vercel.app` → Manual Deploy
7. Browser login: `demo@sentinel.io` / `Sentinel2026!` → open SEV1
8. Open `work/paste/ROUND3_AGENT_F_URLS.md`, replace placeholders with real URLs, paste to Agent F

## Demo credentials
- Email: `demo@sentinel.io`
- Password: `Sentinel2026!`
