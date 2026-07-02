# Aegis — web app

Next.js (App Router) + Tailwind + Framer Motion + Geist. Talks to the FastAPI backend.

## Run

```bash
# 1) start the API (from the repo root)
uvicorn server.app:app --port 8000

# 2) start the web app
cd web
npm install
npm run dev            # http://localhost:3000
```

`next.config.mjs` proxies `/api/*` to the backend (default `http://localhost:8000`, override
with the `API_URL` env var). For the live Cognee-backed recall/erase, start the API with
`AEGIS_BACKEND=cognee`.
