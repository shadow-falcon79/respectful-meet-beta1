# Respectful Meet — Beta development status

## Owner decisions applied
- Profile/VIP capacity is **500**.
- E2EE is the priority for text messages.
- Off-platform contact sharing is blocked locally before encryption until Premium or 20 days for the conversation.
- Real WebRTC audio/video calling is included.
- No fake payment, fake account, fake admin record, or fake successful integration is presented as real.

## Completed in the current development pass
- Real FastAPI-backed auth/session flow remains the source of authentication state.
- Real profile, feed, likes, matches and conversation APIs are wired into the main user UI.
- E2EE identity registration and encrypted text transport remain enabled.
- Local pre-encryption safety gate blocks phone/email/link/external-platform sharing while restricted.
- Server-authoritative external-sharing entitlement endpoint (Premium or 20-day conversation age).
- WebRTC signalling for audio/video calls with authenticated WebSocket sessions.
- Incoming-call inbox only connects for authenticated users.
- Microphone/camera controls, camera switching, hang-up and ICE candidate buffering.
- Real admin Users, VIP capacity/VIP profiles and Reports pages backed by admin APIs.
- VIP creation is a real backend User/Profile/Photo record and is subject to the server-side 500 limit.
- User suspension/unsuspension/deletion and report resolution are wired to backend endpoints.
- Account deletion is a real backend endpoint.
- Old user-facing mock service/data modules were removed from the frontend.
- Old fake admin tables and fake dashboard metrics were replaced by real API data or an explicit unavailable state.
- Demo OTP hint was removed from the user-facing authentication screen.

## Remaining external dependencies (not safely inventable locally)
- Production PostgreSQL and HTTPS/WSS deployment.
- Real email provider credentials for OTP delivery.
- Telegram Stars bot/webhook/payment verification.
- TURN credentials for reliable calls behind restrictive NAT/mobile networks.
- Production object storage/CDN if local storage is not appropriate.
- Identity-verification provider, if required by the final specification.
- Push notification provider.

## Validation
- Backend Python source compiles with `python -m compileall`.
- Full backend pytest suite cannot run in this environment because the required PostgreSQL DB driver/server is unavailable here.
- Full frontend build cannot run here because dependencies are not installed and this environment cannot fetch the npm registry. `npm ci` must be run in a networked CI/development environment before release.

## E2EE limitation
A genuine E2EE backend cannot inspect plaintext messages. Therefore the off-platform content gate runs before encryption on the sender device. This is the deliberate architecture for the owner's E2EE priority; the backend only authorizes whether the gate may be relaxed.

## Telegram Stars + Gmail SMTP integration pass (2026-08-31)

Implemented in code:
- Telegram XTR invoice-link creation from the authenticated Premium checkout.
- Backend-owned plan price validation.
- `pre_checkout_query` validation and response.
- `successful_payment` fulfillment and Premium activation.
- Idempotent payment processing using payment status + unique Telegram charge id.
- Telegram Stars refund service and admin refund endpoint.
- Telegram webhook secret-token validation.
- Admin payment listing.
- Gmail SMTP transactional OTP provider via the official `/v3/smtp/email` API.
- Production-safe secret configuration examples and setup documentation.

Not yet production-connected because the project does not yet have a public HTTPS backend URL and a Gmail SMTP API key/sender configured. The Telegram token from the owner's document is intentionally NOT embedded in the ZIP or source code.

## 2026-09 notification and production audit
- Added notification API, Web Push device registration, VAPID delivery path and in-app notification center.
- Added automatic engagement/re-engagement scheduling with per-user timezone, activity heartbeat and a hard 10/day communication ceiling.
- Added multilingual guidance content for all 11 supported UI languages.
- Added admin broadcast and a dedicated single notification worker process.
- Ads remain intentionally mock/deferred until the production ad provider is selected; no ad production integration is required for this deployment phase.
- Production prerequisites remain environment/configuration items: VAPID keys, HTTPS/WSS, email provider, Telegram webhook, TURN, object storage and identity-verification provider.
- Real secrets are never included in the distributable project; use backend/.env.example as the template.


## Deployment preparation update (2026-11-27)

The owner selected a zero-budget beta architecture:
- Vercel for the React/Vite frontend.
- Render Free for the FastAPI Docker backend (sleeping/cold-start limitations accepted for beta).
- Neon PostgreSQL for relational data.
- Existing FastAPI username/password + Argon2id authentication retained; Neon Auth is not part of this migration.

Deployment files added/updated: `render.yaml`, `frontend/vercel.json`,
`frontend/.env.example`, `backend/.env.example`, and
`BETA1_AUTH_STORAGE_DEPLOYMENT.md`. The backend Docker command now uses Render's
`PORT` (10000 fallback), database pool defaults are reduced for a small free
instance, and production validation no longer requires optional SMTP, VAPID,
Telegram, or object-storage credentials unless those features are configured.

Validation in the current offline environment: Python source compilation passed;
two new production-configuration unit tests passed; Vercel JSON and Render YAML
parsed successfully. The full backend test collection is blocked by missing
`psycopg2` and `slowapi` in this environment. `npm ci` timed out while trying
to access the package registry, so the frontend build remains unverified here.
No live deployment or real-device test has been performed yet.
