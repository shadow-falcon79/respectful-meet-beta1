# Respectful Meet

International dating & matchmaking PWA — real FastAPI/PostgreSQL backend,
real React/TypeScript frontend. No feature in this codebase presents mock
or simulated data as real: unavailable data is shown as unavailable, never
fabricated.

**Current phase: private beta, deployment preparation.** The frontend and
backend are connected in code. The selected zero-budget test deployment is
Vercel (frontend) + Render Free (FastAPI backend) + Neon PostgreSQL. The
cloud deployment still needs environment variables and live end-to-end tests.

## Stack

- **Frontend**: React + TypeScript + Vite, dark theme, PWA
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Alembic, username/password
  auth (Argon2id), server-side sessions, optional Telegram Stars, Web Push,
  WebRTC call signalling, end-to-end encrypted text messages

## Repository structure

```
respectful-meet/
├── frontend/    React + TypeScript + Vite app
├── backend/     FastAPI app
└── docs/        Setup guides, security/E2EE notes, owner decisions
```

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in real values, see comments in the file
# point DATABASE_URL at a local PostgreSQL instance, then:
alembic upgrade head
uvicorn app.main:app --reload
```

Run the test suite against a real PostgreSQL test database:

```bash
createdb respectful_meet_test   # once
pytest
```

### Frontend

```bash
cd frontend
cp .env.example .env.local   # set VITE_API_BASE_URL to the backend above
npm install
npm run build   # tsc -b && vite build — run this before every deploy
npm run dev
```

Open `http://localhost:5173`.

## What still needs real external configuration

The code for all of these is implemented and documented; what's left is
supplying real credentials/infrastructure, not writing more code:

1. Production PostgreSQL instance + `alembic upgrade head`.
2. HTTPS frontend and HTTPS/WSS backend hosting.
3. SMTP credentials only if admin OTP is enabled with an admin allowlist.
4. VAPID keys for Web Push (optional for the first beta test).
5. TURN credentials for calls across restrictive NAT/mobile networks.
6. Telegram Stars: bot token + webhook secret + live checkout test.
7. S3-compatible object storage credentials for persistent photos/media; Render Free local storage is ephemeral.
8. `ALLOWED_HOSTS` and CORS set to the real domain(s).
9. Reward-ad provider (e.g. AdMantum) — the ad flow is real code but stays
   in mock/disabled mode in production until a provider is wired in;
   nothing else in the app depends on it.
10. Photo moderation provider (e.g. AWS Rekognition, Hive, Sightengine) —
    same pattern as #9: `PHOTO_MODERATION_ENABLED` stays false, uploads are
    unscreened, until a provider is wired into
    `app/services/photo_moderation_service.py`.
11. Legal review of `frontend/src/pages/legal/TermsOfService.tsx` and
    `PrivacyPolicy.tsx` by counsel licensed in your operating
    jurisdiction(s) — the `[BRACKETED]` fields (entity name, address,
    governing law, retention periods) are placeholders. The structure and
    the technical claims (what's encrypted, what's exported, what's kept)
    are accurate as of this audit; the legal boilerplate is not yet
    reviewed.

See `BETA1_AUTH_STORAGE_DEPLOYMENT.md` for the current Vercel + Render + Neon
setup, `PRODUCTION_AUDIT.md` for the full, itemized audit and
`docs/` for setup guides (`DDOS_AND_HARDENING.md`, `E2EE_SECURITY.md`,
`BACKEND_MASTER_SPEC.md`, `OWNER_DECISIONS.md`).

## Environment variables

See `backend/.env.example` and `frontend/.env.example` for every variable
and what it controls. Real secrets must never be committed — only
`.env.example` files with placeholders belong in the repository (enforced
by `.gitignore`).

## Git

```bash
git init
git add .
git commit -m "Respectful Meet — backend-connected beta"
git branch -M main
git remote add origin <your-private-repo-url>
git push -u origin main
```

Keep the repository **private**. Do not commit `.env` files or secrets.


## Beta authentication update
Regular user authentication is now username + password. Passwords are hashed with Argon2id and sessions remain server-side via HttpOnly cookies. The email OTP flow is retained only for the separate admin authentication flow required by the master specification.
