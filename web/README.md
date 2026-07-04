# Aegis — web app

Next.js (App Router) + Tailwind + Framer Motion + NextAuth + Geist. Talks to the FastAPI
backend. Each signed-in user has their own private profile.

## Run

```bash
# 1) API (from repo root)
uvicorn server.app:app --port 8000

# 2) web app
cd web
cp .env.local.example .env.local      # then edit it (see below)
npm install
npm run dev                           # http://localhost:3000
```

## Auth setup

Sign-in is handled by NextAuth. Set these in `web/.env.local`:

- `NEXTAUTH_SECRET` — required. Generate: `openssl rand -base64 32`
- `NEXTAUTH_URL=http://localhost:3000`
- `API_URL=http://localhost:8000`

**Guest login** works out of the box (no setup) so you can explore immediately.

**Google login** (optional):
1. Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID (Web app).
2. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
3. In `.env.local` set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and
   `NEXT_PUBLIC_GOOGLE_ENABLED=true`.

## Notes

- `/backend/*` is proxied to the FastAPI API (`API_URL`); `/api/*` is reserved for NextAuth.
- Each request sends the signed-in user's id, and the backend serves that user's isolated
  profile (persisted under `server/_userdata/`). New profiles start empty.
- The Cognee-backed memory ("Ask Aegis" and the safety check's broad assessment) is a single
  shared graph per deployed instance, not per account — see the root README's Architecture
  section for why. For a demo, use one account at a time.
