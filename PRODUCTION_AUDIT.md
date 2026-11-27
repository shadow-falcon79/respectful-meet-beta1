# Respectful Meet — Production Audit & Fixes (2026-09-01)

## 2026-09-02 follow-up: legal/trust, operational, and code-quality hardening

This follow-up closes the three gaps flagged as blocking beta launch in the
2026-09-01 external audit: no legal pages, no data export, no CI, and dead
moderation code. Nothing below replaces the original audit; it's additive.

**Legal / user trust**
- `terms_accepted_at` / `privacy_accepted_at` / `terms_version` added to
  `User` (migration `d3f6a9c1b284`); registration now rejects
  `accept_terms: false` or missing with `400`.
- `GET /api/v1/privacy/export` — full personal-data export (profile,
  photos, likes, matches, blocks, reports, message metadata, subscriptions,
  payments, notifications, calls), rate-limited 5/hour, own-data only.
  Frontend: Settings → "Export my data" (`/privacy/export`) downloads it as
  JSON.
- `frontend/src/pages/legal/{TermsOfService,PrivacyPolicy}.tsx` — full
  draft text (EN/FR), routed at `/legal/terms` and `/legal/privacy`,
  linked from the signup consent checkbox and from Settings. **Still
  needs lawyer review** — entity name/address, governing law, and
  retention periods are `[BRACKETED]` placeholders; the technical claims
  (encryption, export contents, deletion behavior) were cross-checked
  against the actual code.
- Photo moderation abstraction added
  (`app/services/photo_moderation_service.py`), wired into both upload
  endpoints (user + admin/VIP). Same disabled-by-default pattern as
  rewarded ads (`PHOTO_MODERATION_ENABLED=false` until a provider —
  Rekognition/Hive/Sightengine — is configured); fails loudly rather than
  silently passing everything through if misconfigured.
- `content_filter.py` (previously dead code — defined, never called) is
  now applied to the profile bio, the one place it can run server-side
  given messages are E2EE; docstring rewritten to state that scope
  explicitly instead of implying message-level coverage it never had.

**Operational readiness**
- `.github/workflows/ci.yml` — pytest against a real Postgres service
  container, plus `npm ci && npm run build && npm run lint` on every push/PR.
  This replaces `python -m compileall` (syntax-only) with an environment
  that can actually run the 66 backend tests end to end.

**New/updated tests** (backend): `test_privacy.py` (4),
`test_photo_moderation.py` (4), bio content-filter tests in
`test_social.py` (3), consent-rejection test in `test_auth.py` (1).

**Known remaining gaps** (unchanged from 2026-09-01, still open):
identity/anti-catfishing verification is not implemented; rate limiting
and call presence are in-process (need Redis before multi-instance
scaling); legal text needs a licensed-lawyer pass before real users sign up.

---


This audit was performed against the uploaded `respectful-meet-production-ready` source archive, not only against the previous checklist.

## Fixed in this revision

- **Like notification persistence:** the previous flow committed the Like before creating the notification, then failed to commit the notification when there was no reciprocal Like. Notifications are now committed with the Like transaction.
- **Like/Match push delivery:** event notifications are committed before push delivery, so a push failure cannot roll back the in-app notification.
- **Notification localization:** automatic notifications now use the latest registered device language instead of always defaulting to English. Event notification fallbacks were added for LIKE, MATCH, MESSAGE, PAYMENT, SUBSCRIPTION_EXPIRING, REPORT and SYSTEM.
- **Premium expiry warning:** a dedicated worker job now creates an idempotent 24-hour expiry notification and attempts push delivery.
- **Media cleanup scheduling:** the dedicated notification worker now also runs expired chat-media cleanup.
- **Production configuration fail-fast:** production startup now rejects development database URLs, weak/default secrets, localhost CORS, console OTP, missing VAPID credentials, missing Telegram webhook configuration and missing production object-storage credentials.
- **Production object storage:** profile/chat/VIP media can now use S3-compatible object storage (AWS S3, Cloudflare R2 or another compatible provider). Local disk remains available for development/tests.
- **Production readiness probe:** `/api/v1/health/ready` now verifies PostgreSQL connectivity.
- **Rewarded ads safety:** ads can be disabled explicitly; mock ad completion is refused in production and when ads are disabled.
- **Frontend route bug:** `NotificationBootstrap` was previously inserted directly as a child of `<Route>`, which is invalid React Router structure. It is now wrapped in a route element that renders an `<Outlet />`.
- **Delete-account UI bug:** the destructive confirmation button incorrectly said `Close`; it now says `Delete permanently`.

## Verified from source

- Alembic migration chain has a single head: `c7e91f2a4b55` (linear chain of 10 revisions, verified by tracing every `revision`/`down_revision` pair — no forks).
- `.gitignore` excludes real `.env`/`.env.local` files and keeps only `.env.example` templates.
- Gmail SMTP, Telegram Stars, VAPID, WebRTC TURN variables and storage variables are present in configuration/templates.
- E2EE message envelopes are represented in the backend; admin code does not expose message plaintext.
- Guide content exists for all 11 configured application languages.

## Not declared production-ready yet

These require real external configuration or real-device/provider tests and therefore cannot honestly be marked green from source inspection alone:

1. PostgreSQL production instance + `alembic upgrade head`.
2. HTTPS frontend and HTTPS/WSS backend deployment.
3. Gmail SMTP live OTP delivery test.
4. VAPID test on a real Android Chrome device with the app closed.
5. TURN test between two different networks/mobile connections.
6. Telegram Stars live checkout + webhook + refund test.
7. Object-storage credentials, bucket/public URL and real upload/delete test.
8. Frontend dependency installation and `npm run build` in a clean networked environment.
9. Full pytest suite against PostgreSQL.
10. Remaining product/admin scope: richer Settings, complete admin analytics/settings/likes-matches/messages/subscriptions UI, and real identity-verification/ads providers if those features are enabled for launch.

## Test limitation in this audit environment

Backend source compilation succeeds, but the audit environment does not have the PostgreSQL Python driver installed, so pytest collection stops at `ModuleNotFoundError: psycopg2`. The frontend archive did not contain a complete dependency installation; `npm ci --offline` cannot finish because required packages are not cached. Therefore no false "all tests passed" claim is made.


## Deployment configuration update (2026-11-27)

For the zero-budget beta, the production guard was adjusted to require only
core database, strong secret, HTTPS CORS origin, and explicit host settings.
Optional SMTP/admin OTP, VAPID push, Telegram payments, and S3 media credentials
are required only when their corresponding configuration is enabled or partially
set. Render Free uses an ephemeral local filesystem; persistent user media must
use S3-compatible storage before public launch. See
`BETA1_AUTH_STORAGE_DEPLOYMENT.md` for the Vercel + Render + Neon deployment
plan. This does not constitute a production-readiness certification.
