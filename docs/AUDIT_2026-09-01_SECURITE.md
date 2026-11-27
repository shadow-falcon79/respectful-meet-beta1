# Audit professionnel complet — Respectful Meet (2026-09-01)

Audit réalisé par inspection directe du code source réel (backend FastAPI/
PostgreSQL, frontend React/Vite, configuration, déploiement) à la demande du
propriétaire, avant hébergement et ouverture aux utilisateurs réels. Cet
audit fait suite à deux passes de renforcement précédentes documentées dans
`PRODUCTION_AUDIT.md` et `HARDENING_CHANGELOG.md` — il ne les répète pas, il
les complète.

**Méthode :** lecture ligne par ligne de l'authentification, des sessions,
de l'admin, des likes/matches/feed, de la messagerie E2EE, des uploads/
stockage, des paiements Telegram Stars + webhook, des récompenses publicitaires,
de la modération (blocage/signalement), des profils, de la configuration
production, des headers HTTP, du rate limiting, de CORS, du frontend
(recherche XSS/secrets), des dépendances et des index de base de données.

**Constat général :** le code était déjà d'un bon niveau professionnel
(argon2 pour les OTP, tokens de session opaques hashés côté serveur, IDOR
systématiquement vérifié par `current_user.id`, contraintes uniques en
base pour Like/Match/Block/Conversation, chiffrement de bout en bout des
messages, vérification des octets magiques sur les uploads image,
`validate_production_settings()` qui refuse de démarrer en prod avec des
valeurs par défaut, comparaison à temps constant déjà utilisée pour le
postback publicitaire). Ce n'était donc pas un audit « tout est cassé » :
les failles trouvées sont réelles mais ciblées.

---

## 1. Ce qui était vulnérable / fragile

| # | Problème | Fichier | Gravité |
|---|----------|---------|---------|
| 1 | Comparaison du secret webhook Telegram avec `==` au lieu d'une comparaison à temps constant → fuite d'information temporelle exploitable pour deviner le secret octet par octet sur un grand nombre de requêtes. | `app/api/v1/telegram.py` | Moyenne |
| 2 | Le WebSocket d'appel (`/ws/calls`, `/ws/call-inbox`) authentifiait la session sans vérifier `expires_at` — une session expirée (30 jours) mais jamais explicitement déconnectée (logout) pouvait continuer à ouvrir des appels audio/vidéo indéfiniment. | `app/api/v1/calls.py` | Moyenne |
| 3 | `POST /likes` : deux requêtes concurrentes identiques (double-tap, retry réseau, requête envoyée deux fois) passant toutes les deux le contrôle applicatif « existe déjà ? » avant le commit provoquaient une `IntegrityError` non interceptée → **500** brut au lieu d'une réponse idempotente propre. La contrainte unique DB empêchait bien la corruption de données, mais l'API n'était pas robuste à la race explicitement demandée (section 7 du cahier des charges). | `app/api/v1/social.py` | Faible/robustesse |
| 4 | Même problème pour `POST /blocks`. | `app/api/v1/moderation.py` | Faible/robustesse |
| 5 | Plusieurs champs texte libres acceptaient une taille illimitée côté API (prénom, nom, genre, pays, ville à l'inscription et à l'édition de profil ; bio ; liste d'intérêts ; motif/détails de signalement ; clés push `p256dh`/`auth`) — un client pouvait envoyer des chaînes de plusieurs Mo, gonflant le stockage et la mémoire, une surface d'abus/DoS explicitement visée en section 2 et 3. | `app/schemas/auth.py`, `profile.py`, `moderation.py`, `social.py`, `notifications.py` | Faible/abus |
| 6 | Aucune limite globale de taille de requête au niveau applicatif : un corps JSON volumineux pouvait être reçu avant même que Pydantic ne le valide. | `app/main.py` | Faible/défense en profondeur |
| 7 | `.env.example` référençait des variables (`PAYMENT_SECRET`, `AD_PROVIDER_KEY`, `BETA_MODE`, `NO_BETA_USER_WHITELIST`, `REDIS_URL`) **jamais lues nulle part dans le code**. En particulier `BETA_MODE`/`NO_BETA_USER_WHITELIST` laissaient croire à un contrôle d'accès bêta qui n'existe pas réellement côté serveur — risque de fausse confiance avant une ouverture publique. `ADMIN_ALLOWED_EMAILS` était par ailleurs dupliqué. | `backend/.env.example` | Documentation/config trompeuse |
| 8 | (Observation, non corrigée — comportement probablement intentionnel à confirmer) `POST /notifications/push/subscribe` réassigne un enregistrement d'appareil push existant (identifié par son `endpoint`) au compte qui vient de s'abonner, sans vérifier qu'il appartenait déjà à ce compte. C'est le comportement correct pour un changement de compte sur un même navigateur, mais si un `endpoint` de tiers était un jour connu, cela permettrait de faire basculer ses notifications. L'`endpoint` d'un navigateur est une URL secrète à haute entropie, donc le risque réel est faible — signalé pour confirmation produit. | `app/api/v1/notifications.py` | Info — à confirmer |

## 2. Ce qui a été corrigé

1. **`app/api/v1/telegram.py`** — comparaison du secret webhook remplacée par `hmac.compare_digest`.
2. **`app/api/v1/calls.py`** — `_authenticate()` vérifie désormais `expires_at` en plus de `revoked_at`, exactement comme `app.auth.dependencies.get_current_user` utilisé par le reste de l'API REST.
3. **`app/api/v1/social.py`** — `create_like()` intercepte l'`IntegrityError` de la race condition, fait un `rollback()` et renvoie la ressource existante de façon idempotente (201, jamais 500).
4. **`app/api/v1/moderation.py`** — même correction pour `block_user()`.
5. **Bornage des entrées texte** ajouté avec `Field(max_length=...)`, aligné sur les colonnes PostgreSQL existantes (pas de changement de schéma DB nécessaire) :
   - `schemas/auth.py` (`RegisterIn`)
   - `schemas/profile.py` (`ProfileUpdateIn`, y compris nombre max d'intérêts et longueur par intérêt)
   - `schemas/moderation.py` (`BlockIn`, `ReportIn`)
   - `schemas/social.py` (`LikeIn`)
   - `schemas/notifications.py` (`DeviceSubscriptionIn`)
6. **`app/main.py`** — nouveau `MaxBodySizeMiddleware` : rejette avec un `413` propre toute requête dont l'en-tête `Content-Length` dépasse 10 Mo, avant même que le routage/la validation ne s'exécutent. *(Défense en profondeur : ne remplace pas une limite au niveau CDN/reverse proxy, qui reste nécessaire — voir section 4.)*
7. **`backend/.env.example`** — nettoyage : suppression des variables fantômes, doublon `ADMIN_ALLOWED_EMAILS` supprimé, note explicite que le contrôle d'accès admin par allowlist d'e-mails est le **seul** mécanisme de contrôle d'accès existant.
8. **Tests de régression ajoutés** (voir section 3) pour les points 2, 3, 4 et 5.

### Fichiers modifiés

```
backend/app/main.py
backend/app/api/v1/telegram.py
backend/app/api/v1/calls.py
backend/app/api/v1/social.py
backend/app/api/v1/moderation.py
backend/app/schemas/auth.py
backend/app/schemas/profile.py
backend/app/schemas/moderation.py
backend/app/schemas/social.py
backend/app/schemas/notifications.py
backend/.env.example
backend/tests/test_social.py        (2 tests ajoutés)
backend/tests/test_moderation.py    (1 test ajouté)
backend/tests/test_calls_auth.py    (nouveau fichier, 2 tests)
docs/AUDIT_2026-09-01_SECURITE.md   (ce document)
```

Aucune fonctionnalité existante n'a été modifiée dans son comportement
attendu — uniquement des vérifications supplémentaires et une gestion plus
propre des cas limites déjà couverts par les contraintes de base de
données existantes.

## 3. Tests effectués

**Contrainte d'environnement (honnêteté, comme dans l'audit précédent) :**
ce bac à sable d'audit n'a ni PostgreSQL ni accès réseau — `pip install`
échoue (« No matching distribution found »), donc **je n'ai pas pu exécuter
la suite pytest ici**, ni `npm audit` / `pip-audit` pour les dépendances.
Je ne prétends donc pas « tous les tests passent ». Ce qui a été fait :

- Compilation Python (`py_compile`) de **tous** les fichiers modifiés → aucune erreur de syntaxe.
- Relecture manuelle ligne par ligne de chaque endpoint modifié pour vérifier la cohérence avec le reste du code (imports, signatures, types).
- Ajout de **4 tests de régression réels**, écrits dans le style exact de la suite existante (fixture PostgreSQL de `tests/test_auth.py`), prêts à s'exécuter dès qu'une base de test est disponible :
  - `test_like_race_condition_is_idempotent_not_500` — deux requêtes `/likes` concurrentes réelles (threads) sur la même paire → attend `[201, 201]`, jamais de 500.
  - `test_block_race_condition_is_idempotent_not_500` — même test pour `/blocks`.
  - `test_register_rejects_oversized_field` — un prénom de 5000 caractères à l'inscription doit être rejeté en 422.
  - `test_calls_authenticate_rejects_expired_session` / `test_calls_authenticate_accepts_valid_session` — teste directement `_authenticate()` de `calls.py` avec une session expirée puis valide.

**À faire avant mise en production (ne peut pas être fait honnêtement depuis
ce bac à sable) :**
```
cd backend
pip install -r requirements.txt
createdb respectful_meet_test   # ou pointer TEST_DATABASE_URL
pytest -q
pip-audit -r requirements.txt   # dépendances Python vulnérables
cd ../frontend && npm ci && npm audit --production
```

## 4. Problèmes qui restent

- **Champs texte libres de l'admin** (`VipCreateIn` dans `schemas/admin.py`)
  n'ont pas de `max_length` — non corrigé car cet endpoint n'est
  accessible qu'à un compte déjà authentifié ADMIN (risque très réduit),
  mais à borner par cohérence si le temps le permet.
- **`AdminVerifyCodeIn.code`** n'a pas le même validateur « 6 chiffres
  exacts » que `VerifyCodeIn` côté utilisateur normal — un code malformé
  échoue quand même (mismatch de hash) mais avec une erreur 400 générique
  plutôt qu'un 422 propre. Cosmétique, pas une faille.
- **Dépendances (npm/pip)** : je n'ai pas pu exécuter d'audit automatisé
  faute de réseau dans cet environnement. `requirements.txt` et
  `package.json` listent des versions récentes et raisonnables au moment
  de la rédaction (FastAPI 0.115, SQLAlchemy 2.0.35, React 18.3, Vite 5.4)
  sans rien d'exotique ou d'abandonné, mais seul un vrai `pip-audit`/
  `npm audit` fait foi — à lancer en CI avant chaque déploiement (voir
  section 3).
- **Limite de taille de requête basée sur `Content-Length`** : contournable
  en théorie par un client envoyant un corps en `Transfer-Encoding: chunked`
  sans en-tête `Content-Length`. C'est une défense en profondeur utile mais
  pas suffisante seule — la vraie limite doit venir du reverse proxy/CDN
  (voir section 5).

## 5. Éléments qui dépendent de l'hébergement / infrastructure

*(Reprend et confirme les points déjà identifiés dans `PRODUCTION_AUDIT.md`
et `docs/DDOS_AND_HARDENING.md`, qui restent valides et à jour.)*

1. **Protection DDoS volumétrique réelle** : Cloudflare (ou WAF/CDN
   équivalent) devant le domaine backend, avec limite de taille de requête
   au niveau du proxy (en complément du `MaxBodySizeMiddleware` ajouté
   aujourd'hui, pas à sa place).
2. PostgreSQL de production + `alembic upgrade head`.
3. HTTPS sur le frontend et HTTPS/WSS sur le backend.
4. Test d'envoi OTP réel via Gmail SMTP.
5. Test VAPID sur un vrai appareil Android Chrome, application fermée.
6. Test TURN entre deux réseaux/connexions mobiles différents.
7. Paiement Telegram Stars réel (checkout + webhook + remboursement).
8. Identifiants du stockage objet (S3/R2), bucket, URL publique, test réel d'upload/suppression.
9. `npm run build` du frontend dans un environnement réseau propre.
10. Suite pytest complète contre PostgreSQL.
11. Sauvegardes PostgreSQL : fréquence, rétention, **test de restauration réel** (un backup jamais restauré ne doit pas être considéré fiable).
12. Monitoring/alerting externe (taux d'erreur, latence, tentatives de connexion anormales) — les logs structurés JSON existent déjà côté code (`app/core/logging_config.py`), il manque l'agrégateur (Sentry, Datadog, CloudWatch, etc.) côté infra.

## 6. À configurer précisément au moment du déploiement

- `ALLOWED_HOSTS` → vrai(s) nom(s) d'hôte de production.
- `CORS_ORIGINS` → origine HTTPS réelle du frontend.
- Remplacer `https://api.YOURDOMAIN.com` dans `frontend/netlify.json` et `frontend/public/_headers` par le vrai domaine backend.
- `SECRET_KEY` → valeur aléatoire ≥ 32 caractères, générée pour la prod (jamais réutilisée du `.env` de dev).
- `ADMIN_ALLOWED_EMAILS` → e-mails réels des administrateurs, uniquement dans le `.env` du serveur.
- Toutes les clés/API tierces (Gmail SMTP, Telegram, VAPID, stockage objet, `ADS_POSTBACK_SECRET`) → valeurs réelles de production, jamais commitées.
- `ADS_MOCK_MODE=false` avant toute activation de `ADS_ENABLED=true` en prod (déjà bloqué par `validate_production_settings()` si oublié).
- Rotation immédiate de tout secret qui aurait pu transiter par un canal non sécurisé avant ce jour.

## 7. Verdict

L'application n'était pas dans un état alarmant — les fondations
(authentification par OTP + session opaque, IDOR systématiquement
vérifié, E2EE, contraintes DB, validation prod fail-fast) étaient déjà
solides. Les corrections apportées aujourd'hui referment une fuite
temporelle sur le webhook de paiement, un bug de session qui n'expirait
jamais sur les appels, deux races non gérées proprement, une surface
d'abus par payloads surdimensionnés, et une documentation d'environnement
trompeuse. Ce qui reste dépend uniquement de l'infrastructure choisie au
moment de l'hébergement (liste section 5) — rien de bloquant côté code.
