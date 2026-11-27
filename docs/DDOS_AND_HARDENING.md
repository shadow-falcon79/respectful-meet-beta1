# Protection DDoS et renforcement production

Ce document explique, honnêtement, ce qui protège déjà l'application au
niveau du code, et ce qui **ne peut pas** être résolu par du code seul —
pour que rien ne soit présenté comme réglé alors que ça ne l'est pas.

## Ce qui est fait dans le code (niveau application)

- **Rate limiting global** (`app/core/rate_limit.py`, slowapi) : 300
  requêtes/minute par IP par défaut sur toute l'API, avec des limites plus
  strictes sur les endpoints sensibles :
  - OTP (demande) : 10/minute/IP
  - OTP (vérification) : 20/minute/IP
  - Inscription : 10/minute/IP
  - Paiement (création de facture) : 20/minute/IP
  - Envoi de message : 60/minute/IP
  - Upload de photo (profil + chat) : 20/minute/IP
  - Toute requête au-delà reçoit un `429 Too Many Requests`.
- **Anti brute-force OTP par email** (déjà présent avant cette passe,
  `app/services/otp_service.py`) : 3 codes/15 min par adresse email, en plus
  de la limite par IP ci-dessus — un attaquant ne peut ni matraquer une
  adresse, ni tourner sur plusieurs adresses depuis la même IP.
- **Lecture bornée des uploads** : chaque endpoint d'upload (photo de
  profil, photo de chat) lit au maximum `MAX_IMAGE_SIZE_BYTES + 1` octets,
  jamais le fichier entier sans limite — empêche un fichier énorme
  d'épuiser la mémoire/le disque du serveur.
- **Validation du Host header** (`TrustedHostMiddleware`) : rejette les
  requêtes dont l'en-tête `Host` ne correspond pas à `ALLOWED_HOSTS` —
  bloque les attaques de type Host-header injection / cache poisoning.
- **Gestionnaire d'exception global** : toute erreur non prévue renvoie un
  JSON `500` générique et est loguée, sans jamais exposer de stack trace au
  client. L'application ne plante jamais un worker sur une requête
  malformée.
- **Headers de sécurité sur chaque réponse** (backend et frontend) : HSTS,
  CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
  Permissions-Policy.
- **Compression GZip** sur les réponses de l'API pour réduire la bande
  passante et accélérer le chargement sur mobile.
- **Pool de connexions PostgreSQL dimensionné** (`pool_size=10,
  max_overflow=20, pool_recycle=1800`) avec `pool_pre_ping` pour ne jamais
  servir une requête sur une connexion morte.

## Ce que le code seul ne peut pas faire : la couche réseau/CDN

Un rate-limiter applicatif, même bien fait, tourne **après** que la requête
a atteint ton serveur — il consomme déjà de la bande passante, du CPU pour
le TLS handshake, une connexion. Une vraie attaque DDoS volumétrique
(des dizaines de milliers de requêtes/seconde depuis un botnet) doit être
absorbée **avant** d'arriver au processus Python, sinon le serveur tombe
même si chaque requête individuelle est ensuite rejetée en 429.

Pour ça, il faut une couche devant le backend — aucune app FastAPI, aussi
bien codée soit-elle, ne s'en passe en production réelle :

- **Cloudflare** (le plus simple à mettre en place avec Netlify) : proxy
  DNS orange-cloud activé sur le sous-domaine `api.tondomaine.com`, mode
  "Under Attack" disponible en cas de pic, WAF géré, protection DDoS
  incluse même sur le plan gratuit.
- Alternative : **AWS Shield/CloudFront**, **Fastly**, ou le WAF intégré
  de l'hébergeur choisi pour le backend (Railway, Render, Fly.io ont tous
  des options réseau différentes — à vérifier au moment du choix).
- Le frontend est déjà servi par Netlify, qui a sa propre protection
  edge/CDN intégrée — rien à ajouter côté frontend au-delà des headers déjà
  configurés dans `netlify.json`.

**Sans cette couche, le rate-limiting applicatif reste utile** (il stoppe
le brute-force, le scraping agressif, les bots mal élevés) **mais ne
protège pas contre un vrai DDoS volumétrique.** C'est la vérité technique,
pas une case à cocher qu'on peut remplir depuis le code seul.

## Checklist de mise en production

1. `ALLOWED_HOSTS=api.tondomaine.com` dans le `.env` de prod (jamais `*`).
2. Domaine backend derrière Cloudflare (proxy activé) avant d'ouvrir l'accès public.
3. Remplacer `https://api.YOURDOMAIN.com` par le vrai domaine dans
   `frontend/netlify.json` et `frontend/public/_headers`.
4. Si tu passes un jour à plusieurs instances backend, configurer
   `RATE_LIMIT_STORAGE_URL` vers un Redis partagé — sinon chaque instance a
   son propre quota et la limite globale devient inefficace.
5. Vérifier `validate_production_settings()` : le serveur refuse de
   démarrer si un secret par défaut, une URL localhost, ou `ALLOWED_HOSTS=*`
   traîne encore.
