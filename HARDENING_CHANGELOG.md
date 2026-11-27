# Passe de renforcement production — 2026-09-01

Objectif : combler les points relevés lors de l'audit précédent (82/100)
pour la vitesse, la stabilité et la sécurité (brute force, DDoS applicatif,
DoS par upload, headers manquants).

## Backend

- **Rate limiting global** (`app/core/rate_limit.py`, nouveau) : 300 req/min/IP
  par défaut sur toute l'API, limites renforcées sur OTP, inscription,
  paiement, envoi de message, upload — via `slowapi`. Câblé dans `main.py`
  avec réponse `429` propre (pas de fuite d'info, `Retry-After` inclus).
- **Headers de sécurité HTTP** (`app/core/security_headers.py`, nouveau) :
  HSTS (prod uniquement), CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy, Cross-Origin-Resource-Policy sur
  chaque réponse.
- **Validation du Host header** (`TrustedHostMiddleware`) : nouveau réglage
  `ALLOWED_HOSTS`, vérifié par `validate_production_settings()` (refuse de
  démarrer en prod avec `*`).
- **Gestion d'erreurs globale anti-crash** : tout exception non prévue →
  `500` JSON générique + log structuré, jamais de stack trace exposée au
  client. Idem pour les erreurs de validation (`422`) et les `HTTPException`.
- **Logging structuré** (`app/core/logging_config.py`, nouveau) : JSON en
  production (exploitable par un agrégateur de logs), texte lisible en dev.
- **Compression GZip** sur les réponses API (fluidité mobile).
- **CORS resserré** : méthodes et headers explicites au lieu de `"*"`.
- **Pool de connexions PostgreSQL dimensionné** (`pool_size`,
  `max_overflow`, `pool_recycle`, `pool_timeout`) au lieu des valeurs par
  défaut — meilleure tenue en charge, pas de connexions mortes.
- **Correctif DoS upload** : `POST /profiles/me/photos` lisait le fichier
  entier en mémoire sans limite avant validation (contrairement à l'upload
  de message, déjà borné). Corrigé pour lire au maximum `8 Mo + 1 octet`,
  comme le reste de l'app.
- Nouvelles variables `.env` : `ALLOWED_HOSTS`, `RATE_LIMIT_STORAGE_URL`
  (voir `backend/.env.example`).

## Frontend

- **`netlify.json`** (nouveau) : headers de sécurité (HSTS, CSP, etc.) +
  rewrite SPA — sans lui, un rafraîchissement de page sur une route comme
  `/profile` renvoyait une 404 sur Netlify.
- **`public/_headers`** (nouveau) : même protection pour un hébergement
  Netlify/Cloudflare Pages en alternative à Netlify.
- **`vite.config.ts`** : sourcemaps désactivées en production (ne pas
  exposer le code source lisible), découpage du bundle React en chunk
  séparé pour un cache plus efficace et un chargement plus rapide.

## Documentation

- **`docs/DDOS_AND_HARDENING.md`** (nouveau) : explique précisément ce que
  le code protège (brute force, flood applicatif, upload, headers) et ce
  qui nécessite une couche réseau/CDN (Cloudflare devant le backend) pour
  un vrai DDoS volumétrique — pas de fausse promesse de protection totale
  "dans le code".

## Ce qui reste à faire une fois en ligne (config, pas du code)

1. Activer Cloudflare (ou équivalent) devant le domaine backend.
2. Remplacer `https://api.YOURDOMAIN.com` dans `frontend/netlify.json` et
   `frontend/public/_headers` par le vrai domaine.
3. Renseigner `ALLOWED_HOSTS` en prod avec le vrai hostname.
4. Suivre le reste de la checklist déjà connue : PostgreSQL prod, Gmail SMTP
   live, VAPID, TURN, stockage objet (voir `PRODUCTION_AUDIT.md`).
