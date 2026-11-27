# Respectful Meet — Cahier des charges maître (Backend réel + Monétisation + i18n)

**Statut** : document de référence unique, consolidé à partir de 4 cahiers fournis séparément (audit initial, plan de phases, appels audio/vidéo, paiements Telegram + i18n). Remplace tous les documents précédents pour la phase backend — en cas de divergence entre un ancien message et ce document, **ce document fait foi**.

**Règle d'or du projet** : le frontend existant (validé, responsive, gelé) est la référence visuelle. On ne le refait pas. On construit le backend et on connecte progressivement, module par module, sans jamais casser l'existant sans prévenir.

---

## 0. Objectif général

Transformer le prototype (frontend mocké + backend Phase 1/2 partiel) en une vraie application testable en **bêta privée** (le propriétaire + quelques amis), avec persistance réelle, avant ouverture publique.

Priorités dans l'ordre (règle absolue) :
1. Sécurité
2. Exactitude
3. Vraie persistance des données
4. Authentification
5. Paiements vérifiés
6. Stabilité
7. Tests
8. Évolutivité
9. Performance
10. Vitesse de développement

Chaque fonctionnalité livrée doit être étiquetée **[REAL]**, **[MOCK]**, **[PARTIAL]** ou **[NOT IMPLEMENTED]** — ne jamais présenter un mock comme terminé.

---

## 1. Frontend actuel + responsive

- Le frontend (app utilisateur 4 onglets + dashboard admin 12 modules) est **gelé visuellement**. Ne pas le redessiner.
- Mocks existants à identifier et remplacer progressivement, un par un, sans casser le reste : `mockAuthService`, `mockFeedService`, `mockLikeService`, `mockChatService`, `mockProfileService`, `mockSubscriptionService`, `mockDailyLimitService`, `vipStore`, données `mock/admin.ts`.
- Le responsive (mobile référence + tablette/desktop) est déjà fait — le préserver.
- **À ajouter au frontend** (pas encore fait) : interface des appels audio/vidéo (boutons, écrans, quotas, modale Premium requis) — voir section 10. Et l'i18n complète 11 langues — voir section 15.

---

## 2. Backend réel et API

**Stack** : FastAPI + SQLAlchemy + PostgreSQL + Alembic + Pydantic. Redis en option plus tard (cache, rate limiting, OTP, sessions, tâches, chat) — ne pas l'ajouter avant d'en avoir besoin.

**Portabilité — exigence forte** : le backend ne doit dépendre d'aucun fournisseur précis.
- Ne pas coupler le backend à Vercel ou à des fonctionnalités propriétaires.
- Doit pouvoir tourner : en local, sur un VPS, sur Oracle Cloud, sur un autre cloud — sans réécriture.
- Toute configuration sensible passe par variables d'environnement (`.env`, jamais committé ; `.env.example` avec placeholders uniquement).

Variables d'environnement prévues :
```
DATABASE_URL=
REDIS_URL=
JWT_SECRET / SECRET_KEY=
STORAGE_URL / STORAGE_ENDPOINT=
STORAGE_BUCKET=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
PAYMENT_SECRET=
AD_PROVIDER_KEY / AD_SECRET=
BETA_MODE=true
NO_BETA_USER_WHITELIST=
ADMIN_ALLOWED_EMAILS=
```

**Architecture couches** : API → Services → Repository/Data Access → Database. Ne jamais disperser les requêtes DB dans les routes/composants — permet de changer de DB plus tard sans réécrire l'appli.

**Routes API structurées** (préfixe `/api/`) :
```
/api/auth/*          /api/users/*         /api/profiles/*
/api/photos/*        /api/feed/*          /api/likes/*
/api/matches/*       /api/chats/*         /api/messages/*
/api/notifications/* /api/subscriptions/* /api/payments/*
/api/reports/*       /api/admin/*         /api/calls/*
```
Prévoir pagination, filtres, tri, codes HTTP appropriés, réponses cohérentes, `GET /health`.

**Structure de dossiers backend recommandée** (adaptée à l'existant, ne pas tout casser) :
```
backend/app/
├── users/  profiles/  matches/  messages/  media/
├── subscriptions/  payments/  limits/  advertisements/
├── calls/  notifications/  storage/  visibility/  security/
└── config/
```

---

## 3. Comptes, profils, Feed, Likes et Matchs

**Auth** (déjà en partie construite en Phase 1/2 — email + OTP à 6 chiffres, sans mot de passe, session par cookie httpOnly). Compléter avec :
- `POST /api/auth/register`, `/login` (déclenche OTP), `/logout`, `GET /auth/me`
- Rôles minimum : `USER`, `ADMIN` (`MODERATOR` en option plus tard)
- Protection brute force / spam OTP / abus déjà spécifiée en Phase 2, à conserver
- Âge minimum **18 ans**, vérifié côté serveur — non négociable (cf. échanges précédents)

**Profils** : champs déjà présents côté frontend (prénom, nom, date de naissance, genre, pays, ville, bio, intérêts, détails). Jusqu'à **3 photos par profil** (déjà la règle frontend). `GET/POST/PATCH /api/profiles`, upload photo via `StorageService` (voir section 12).

**Feed / Likes / Matchs** :
- `GET /api/feed` (respecte visibilité — section 11), `POST /api/likes`, `GET /api/likes/received`, `GET /api/matches`
- Un like ne doit jamais créer de doublon (contrainte unique `from_user_id, to_user_id`)
- Match = like mutuel → conversation automatiquement débloquée (gratuite, hors quota — section 6)
- Blocage et signalement rattachés à cette zone (`Block`, `Report`)

**VIP** : géré depuis l'admin (déjà mocké avec upload photo réel côté frontend). Un profil VIP doit être **strictement indiscernable** d'un profil normal côté utilisateur (aucun badge, aucune mention). Capacité max 500, appliquée côté backend (pas seulement frontend).

---

## 4. Free / Premium — hiérarchie et limites

```
Free → Premium 1 jour → Premium 7 jours → Premium 1 mois → Premium 1 an
```
Premium plus long = plus d'avantages (quotas, visibilité), **mais aucun plan ne garantit un match**.

| Action | Free | Premium |
|---|---|---|
| Likes / jour | 20 | 100 |
| Messages | 2 gratuits par nouvelle personne, puis pub ou blocage | 100 envoyés / jour (tous destinataires confondus, reçus non comptés) |
| Match → conversation | Toujours gratuite, hors quota | Toujours gratuite, hors quota |
| Photos envoyées en chat | Via publicité récompensée | 10/jour (configurable) |
| Vidéos envoyées en chat | Premium uniquement | Autorisé, limité en taille/durée de conservation |
| Appels audio/vidéo | Démo 5 secondes (une seule fois, contrôlée serveur) | Quota minutes selon plan — section 10 |

**Principes non négociables** :
- Une limite atteinte ne bloque jamais toute l'app — le Feed reste consultable, les profils restent visibles, les likes/matchs reçus continuent d'arriver.
- Tous les compteurs (`likesToday`, `messagesToday`, `messagesPerConversation`, `adUnlocksToday`, `photosToday`, `videosToday`, `callMinutesToday`) sont **côté serveur**, basés sur l'heure serveur — jamais sur l'heure du téléphone.
- Un `LimitService` central expose `canLike(user)`, `canSendMessage(user, conversation)`, `canSendPhoto(user)`, `canStartCall(user)` — pas de règles éparpillées dans 30 fichiers.
- Quand une limite est atteinte, toujours proposer une solution : regarder une pub, passer Premium, ou attendre le renouvellement — jamais un simple blocage sec.

---

## 5. Plans Stars

| Plan | Prix | Quota appels (audio+vidéo, commun) |
|---|---|---|
| 1 jour | ⭐ 150 | 15 min/jour |
| 7 jours | ⭐ 300 | 45 min/jour |
| 1 mois | ⭐ 400 | 90 min/jour |
| 1 an | ⭐ 3 800 | 300 min/jour |

Ces valeurs vivent **uniquement** dans la configuration backend centralisée (`SUBSCRIPTION_PLANS`), jamais dupliquées en dur dans plusieurs composants frontend — le frontend les récupère via l'API.

Minutes d'appel non cumulables d'un jour à l'autre (reset total, pas de report).

---

## 6. Limites et compteurs (détail messages)

- Nouvel utilisateur : **2 messages gratuits par personne/conversation** (pas une limite globale — l'utilisateur peut démarrer plusieurs conversations, 2 messages gratuits chacune).
- Au-delà : publicité récompensée pour débloquer des messages supplémentaires avec **cette** personne (nombre configurable), jusqu'à une limite de déblocages publicitaires/jour (`maxAdMessageUnlocksPerDay`, configurable).
- Dès qu'il y a **match**, la conversation devient intégralement gratuite, sans lien avec la règle des 2 messages.
- Premium : 100 messages envoyés/jour, tous destinataires confondus (pas 100 par personne). Les messages reçus ne comptent jamais.
- Protection anti-spam indépendante du quota commercial : détection d'envoi trop rapide, répétitif, comportement automatisé, envoi de masse.

---

## 7. Publicités récompensées

Flux obligatoire :
```
Action bloquée → Regarder pub → Pub terminée → Fournisseur confirme la récompense
→ Backend valide → Déblocage
```
Le frontend **ne peut jamais** déclarer lui-même `adWatched = true`. Enregistrer chaque récompense (`ad_rewards` : `userId`, `rewardType`, `createdAt`, `expiresAt`, `status`).

---

## 8. Messages et déblocages

Voir section 6 pour la logique. Côté données : `conversations`, `messages` (type texte/média, timestamps, statut lu/non lu, pagination). Blocage utilisateur empêche l'envoi dans les deux sens.

---

## 9. Photos/vidéos dans le chat + suppression après 7 jours

- Médias de conversation séparés du texte : supprimer une photo ne supprime jamais le message texte associé.
- Chaque média a `uploadedAt` et `expiresAt`.
- **Photos : conservation 7 jours**, puis suppression automatique (fichier + référence DB) par tâche périodique.
- **Vidéos** : durée de conservation configurable séparément (`VIDEO_RETENTION_DAYS`).
- Avant stockage : validation MIME réelle (jamais confiance à l'extension du nom de fichier), taille max, compression/redimensionnement, suppression des métadonnées inutiles (EXIF).
- Suppression manuelle possible par l'utilisateur avant expiration.
- Nettoyage automatique périodique : médias expirés, fichiers orphelins, fichiers liés à des messages supprimés.

---

## 10. Appels audio et vidéo + quotas

**Règle de démonstration nouvel utilisateur** : un appel (audio ou vidéo) de démonstration, **5 secondes maximum**, terminé automatiquement, puis message clair invitant à Premium. Contrôlé côté serveur pour empêcher la répétition (changement d'heure, réinstallation, nouveau compte, etc.).

**Quota Premium** : audio et vidéo partagent **un seul portefeuille de minutes/jour** selon le plan (tableau section 5). Non cumulable d'un jour à l'autre.

**Technique** : WebRTC pour le flux temps réel peer-to-peer ; le backend gère authentification, autorisation, signalisation, quotas, début/fin d'appel. **Aucun enregistrement automatique** des appels (ni audio ni vidéo) — confidentialité, coût, risque.

**Frontend à construire (pas encore fait)** :
- Boutons 📞/🎥 dans chaque conversation et sur les profils, selon droits
- Vérification systématique du droit d'appeler côté backend avant de lancer l'appel (jamais décidé par le frontend seul)
- Écrans : appel audio, appel vidéo, appel entrant (accepter/refuser), avec durée, micro/caméra ON-OFF, changement de caméra, fin d'appel
- Affichage du quota restant quand pertinent (pas besoin d'un compteur permanent partout)
- Gestion : connexion faible, reconnexion, appel interrompu, permissions micro/caméra refusées
- Composants indicatifs : `components/calls/*`, `services/calls/{callApi,webrtc,signaling}.ts`, `pages/calls/*` — structure à adapter à l'existant
- Endpoints : `POST /api/calls/check|start|accept|reject|end`, `GET /api/calls/quota`
- Le tout doit rester responsive (mobile/tablette/desktop) et ne pas casser l'existant

---

## 11. Sécurité et détection des numéros, liens et contenus interdits

Chaque message est analysé **côté backend avant envoi** (jamais une simple vérification frontend). Contenu bloqué si détection de :
- Numéros de téléphone, y compris variantes obfusquées (espaces, points, tirets, préfixes internationaux)
- Liens externes (`http://`, `https://`, `www.`) et liens vers plateformes de communication configurées comme interdites
- Mots-clés liés au contournement de la plateforme (WhatsApp, Telegram, "contact externe", email, identifiants externes), y compris variantes évidentes (`w h a t s a p p`, `whats-app`...)
- Adresses email et autres identifiants externes (règles configurables)

Le message refusé n'est jamais transmis au destinataire ; message clair affiché à l'expéditeur. Prévoir normalisation du texte avant analyse pour limiter les faux positifs — ne pas bloquer des conversations légitimes.

---

## 12. Photos/fichiers — stockage (rappel technique)

- Jamais d'image stockée directement dans PostgreSQL — `StorageService` abstrait (permet de changer de fournisseur sans réécrire l'app).
- Fonctions : upload, suppression, remplacement, validation type/taille, nommage sécurisé, compression/redimensionnement.
- Ne jamais faire confiance au nom de fichier envoyé par le client.

---

## 13. Système de visibilité/recommandation

`VisibilityService` combine : activité récente, complétion du profil, interactions/réponses, qualité du profil, régularité d'utilisation, niveau Premium. Premium (surtout les plans longs) obtient une **priorité**, jamais une **garantie**. Un utilisateur Free reste toujours découvrable, y compris après épuisement de ses likes du jour.

---

## 14. Paiements Stars et vérification du solde

Flux complet :
```
Choix du plan → Vérification du solde Stars → si insuffisant : proposer l'achat
officiel de Stars puis revenir automatiquement au plan sélectionné (contexte
conservé) → Paiement Telegram Stars → Confirmation Telegram → Backend vérifie
→ Transaction enregistrée → Premium activé
```
- Le frontend ne décide **jamais** seul qu'un paiement est valide (`paymentSuccess = true` côté client n'active rien).
- Idempotence stricte : une même confirmation reçue plusieurs fois n'active jamais Premium deux fois.
- Historique complet : `paymentId, userId, telegramUserId, plan, starsAmount, paymentProvider, status, createdAt`.
- Expiration automatique (`now >= expiresAt` → repasse Free) sans jamais supprimer compte/profil/matchs/conversations/historique.
- Liaison compte Telegram ↔ compte Respectful Meet, avec vérification qu'un utilisateur ne peut pas lier le Telegram de quelqu'un d'autre.

---

## 15. Bot Telegram

Bot dédié Respectful Meet. Menu principal après `/start` : 👑 Premium · ⭐ Mon compte · 💳 Acheter Premium · 🌍 Langue · ❓ Aide. Permet de consulter les plans et lancer le paiement. Une **Mini App Telegram** est envisageable plus tard, mais doit utiliser le même backend — jamais une logique métier séparée. Token du bot **uniquement** en variable d'environnement (`TELEGRAM_BOT_TOKEN`), jamais dans le code ni Git — fourni par le propriétaire au moment venu.

---

## 16. 11 langues internationales

Anglais (en) · Français (fr) · Espagnol (es) · Portugais (pt) · Arabe (ar) · Allemand (de) · Italien (it) · Russe (ru) · Chinois simplifié (zh-CN) · Japonais (ja) · Turc (tr).

- Détection automatique (langue téléphone/navigateur) avec **anglais en fallback** si non supportée ; sélection manuelle toujours possible ; préférence sauvegardée en `user.language`, prioritaire une fois connecté.
- Traductions séparées du code (`i18n/{en,fr,es,...}.json`), clés type `premium.buy` — jamais de texte en dur dans les composants.
- **RTL complet pour l'arabe** : alignement, menus, boutons, icônes directionnelles, marges, conversations, formulaires, navigation, modales, pages Premium.
- Messages backend traduisibles par code (`PREMIUM_REQUIRED`, `PAYMENT_SUCCESS`, `INSUFFICIENT_STARS`, `CALL_LIMIT_REACHED`, etc.) — le frontend affiche la traduction correspondante.
- Couverture exhaustive : inscription, connexion, profil, Feed, Likes, Matchs, Messages, Photos, Appels, Premium, Paiements, Stars, Publicités, Notifications, Paramètres, sécurité, signalements, blocage, erreurs, confirmations, suppression, expiration, aide.
- Responsive à revalider avec les 11 langues (textes plus longs en allemand notamment) — aucun bouton ne doit déborder.
- Bot Telegram dans la même liste de langues au minimum.

---

## 17. Notifications

Types : nouveau like, nouveau match, nouveau message, paiement, abonnement, expiration proche, signalement (admin). Architecture pensée pour ajouter plus tard push/email/Telegram sans réécrire. Notifications intelligentes de limite ("vous avez atteint vos likes", "regardez une pub", "découvrez Premium", "abonnement expire bientôt").

---

## 18. Stockage et nettoyage automatique

Séparation stricte : PostgreSQL (données structurées + références médias) / stockage fichiers indépendant (photos, vidéos temporaires). Tâche périodique de nettoyage (médias expirés, orphelins, liés à des messages supprimés). Contrôle des coûts par niveau de consommation : faible (texte, likes, matchs, profils) / moyenne (photos, vidéos temporaires) / forte (appels, trafic réseau) — d'où l'absence d'enregistrement des appels et la compression systématique des médias.

---

## 19. Administration / Dashboard admin

**Authentification admin — obligatoire, distincte de l'auth utilisateur.**

`/admin` ne doit **jamais** donner accès au dashboard directement. Flux imposé :
```
/admin/login → email saisi → backend vérifie contre une liste d'emails
autorisés (ADMIN_ALLOWED_EMAILS, variable d'environnement, jamais dans le
frontend, jamais codé en dur) → email non autorisé : "Access denied", aucun
OTP envoyé → email autorisé : génération OTP → envoi par email (via le
même EmailService que l'auth utilisateur) → vérification OTP (expiration
courte, tentatives limitées, usage unique) → session ADMIN distincte,
cookie httpOnly/Secure en production → /admin
```
- Rôle `ADMIN` porté par le modèle `User` (ou table dédiée) — le frontend ne décide jamais `isAdmin = true`.
- **Chaque route `/api/v1/admin/*` vérifie `authenticated AND role == ADMIN` côté backend**, sans exception. Un bouton caché en React n'est jamais une protection.
- Journalisation obligatoire : connexions admin + actions sensibles (suspension, suppression, modération, modification Premium, changement de configuration) → table `AdminAction`.
- Déconnexion, expiration de session, rate limiting et anti-brute-force sur l'OTP admin, comme pour l'auth utilisateur.
- La ou les adresses admin autorisées sont fournies par le propriétaire directement dans son `.env` local (jamais dans un fichier versionné, jamais dans ce document).

Le frontend possède déjà un dashboard admin (mocké) — **ne pas le refaire**, construire les API réelles derrière : Users, Profiles, VIP (upload photo déjà fonctionnel en mock, capacité 100 à appliquer réellement), Reports, Messages/modération, Subscriptions, Payments, Notifications, Analytics, Settings, Limits, Advertisements, Calls, Storage.

---

## 20. Protection anti-contournement et anti-abus

Le backend doit rester l'autorité unique face à toute tentative de : changer l'heure du téléphone, vider le localStorage, modifier le JavaScript/React, appeler l'API directement, envoyer une fausse récompense publicitaire, envoyer un faux statut Premium, envoyer un fichier surdimensionné ou de mauvaise extension, contourner les filtres de messages. Prévoir rate limiting, protection brute force, validation systématique des fichiers, vérification des permissions à chaque endpoint sensible.

---

## 21. Migration et sauvegardes

- Sauvegarde régulière : base de données + médias + configuration + migrations.
- Le projet ne doit dépendre d'aucun hébergeur comme source de vérité : `Serveur A → Backup → Export → Serveur B → Import`, sans perte (utilisateurs, profils, matchs, conversations, abonnements, transactions).
- Identifiants utilisateurs stables à travers une migration (jamais recréés).
- Abonnements/paiements actifs préservés lors d'une migration (jamais réinitialisés).
- Migrations Alembic versionnées, historique propre.

---

## 22. Tests et critères de validation

**Tests fonctionnels minimum** : auth, inscription, connexion, permissions, profils, likes, matchs, chat, abonnements, paiements, admin, sécurité — unitaires + tests API.

**Scénario manuel de référence** :
```
User A créé → User B créé → A like B → B like A → Match créé
→ Message envoyé → A achète abonnement → Telegram confirme
→ Backend vérifie → Subscription ACTIVE
```

**Tests de sécurité à exécuter volontairement** : modifier l'heure du téléphone, modifier le localStorage, modifier le JS, appeler l'API directement, envoyer une fausse récompense pub, un faux statut Premium, un fichier énorme ou de mauvaise extension, tenter de contourner les filtres de message — le backend doit résister à chaque cas.

**Tests de charge progressifs** : 10 → 50 → 100 → 500 → 1000 utilisateurs simulés, en surveillant CPU/RAM/DB/stockage/réseau/temps de réponse.

---

## 23. Déploiement et maintenance

Environnements : `LOCAL → TEST/STAGING → BÊTA PRIVÉE → PRODUCTION`. Ne jamais tester des changements importants directement en production.

**Hébergement** :
- Frontend : Netlify (React/Vite) — choix retenu pour la Beta 1.
- Code : GitHub privé.
- Backend : FastAPI standard et portable, **non couplé à Vercel**, déplaçable vers Oracle Cloud / VPS / autre cloud sans réécriture.
- Si un autre hébergeur est utilisé temporairement, cela doit rester strictement optionnel et non structurant.

Livrables attendus : `.env.example`, `Dockerfile`, `docker-compose.yml` (si utile), `README.md` documentant précisément installation, migrations, démarrage, tests, création d'un admin, déploiement.

**Bêta privée** : `BETA_MODE=true` + `NO_BETA_USER_WHITELIST=` pour restreindre l'accès avant lancement public, contrôlé côté backend.

---

## 24. Méthode de travail imposée

1. **Auditer** l'existant avant de toucher au code (architecture actuelle, ce qui est réel vs mock, risques, manques) — livrer cet audit avant tout changement majeur.
2. Proposer un **plan de migration** module par module, attendre validation.
3. Implémenter **un module à la fois** — jamais 100 fichiers d'un coup.
4. Après chaque module : tests, vérification, explication claire de ce qui a changé, liste des fichiers modifiés.
5. Ne jamais casser une fonctionnalité existante sans prévenir explicitement avant.
6. **Ne jamais deviner** une information sensible (token, URL, domaine, clé API, compte) — toujours demander, et préciser : pourquoi c'est nécessaire, où ça doit être configuré, quelle variable d'environnement utiliser. Ne jamais demander de coller un secret en clair dans le code.

**Ordre de développement backend arrêté** :
```
Sauvegarde du frontend actuel → Préparation backend → Base de données
→ Authentification → Utilisateurs + Profils → Likes → Matchs
→ Conversations → Messages → Service central de limites → Free/Premium
→ Abonnements (config) → Paiement Stars → Publicités récompensées
→ Photos (chat) → Stockage + compression → Suppression automatique
→ Sécurité/filtrage des messages → Notifications → Visibilité/classement
→ Appels audio → Appels vidéo → Quotas d'appels → Dashboard Admin (API réelles)
→ i18n 11 langues → Tests → Tests sécurité → Tests de charge
→ Backup + migration → Staging → Production
```

Ne pas commencer par les appels vidéo (le plus impressionnant visuellement) — ils dépendent de tout le reste (comptes, Premium, quotas, WebRTC). Priorité réelle : **Base de données → Auth → Profils → Likes → Matchs → Messages → Limites → Premium → Paiement**, puis seulement ensuite photos et appels.

---

## Annexe — Contexte déjà en place (ne pas reconstruire)

- Backend Phase 1/2 existant : FastAPI + SQLAlchemy + PostgreSQL + Alembic, auth OTP par email (sans mot de passe), sessions cookie httpOnly, 12 tests passants. **Important : "les tests passent" ne veut pas dire "backend terminé".** C'est une bonne fondation technique pour l'auth uniquement — aucune migration Alembic n'a même encore été générée, et tout le reste (BDD sociale, paiements, stockage, appels, limites, modération, admin sécurisé) reste à construire intégralement.
- Frontend : gelé, responsive validé, dashboard admin mocké complet, VIP avec upload photo mock déjà câblé à un store partagé frontend.
- Utilisateur possède actuellement **19 Telegram Stars** pour tester réellement le paiement une fois le système prêt.
- Âge minimum non négociable : **18 ans**, vérifié serveur.
