import SubPageHeader from "../../components/SubPageHeader";
import { useLanguage } from "../../store/LanguageContext";

/**
 * DRAFT LEGAL TEXT — see the note in TermsOfService.tsx. This draft is
 * written to accurately describe what the CODE actually does (cross-checked
 * against the backend models/services during the pre-beta audit), which is
 * the part a lawyer can't do for you — but the retention periods, legal
 * basis wording, and any DPO/EU-representative details still need sign-off
 * from someone qualified in your operating jurisdiction(s), especially if
 * you have EU/UK/California users (GDPR/UK GDPR/CCPA).
 */

const EN = {
  title: "Privacy Policy",
  updated: "Last updated: [DATE]",
  sections: [
    [
      "1. Who controls your data",
      "[COMPANY LEGAL NAME], registered at [REGISTERED ADDRESS], is the data controller for the personal data described here (\"we\", \"us\"). Contact: [PRIVACY EMAIL].",
    ],
    [
      "2. What we collect",
      "Account: email address. Profile: first/last name, date of birth, gender, country, city, bio, interests, photos. Activity: likes, matches, blocks, reports you file. Messages: end-to-end encrypted content (we store the encrypted envelope, not the readable text) plus metadata (who, when, with whom). Payments: subscription plan, Telegram charge reference, amount — we do not see or store payment card details. Device: push-notification tokens, language, timezone, rough platform info. Technical: IP address transiently, for rate-limiting and abuse prevention.",
    ],
    [
      "3. Why we process it (legal basis)",
      "Providing the service you signed up for (contract): account, matching, messaging, calls, subscriptions. Legitimate interest: fraud/abuse prevention, rate limiting, security logging. Legal obligation: retaining payment records for tax/accounting. Consent: marketing notifications, which you can opt out of at any time in Settings.",
    ],
    [
      "4. End-to-end encryption and what that means for us",
      "Text messages are encrypted on your device before they reach our servers, using a key pair we never see. This means we genuinely cannot read your message content, including for moderation — which is why some safety features (like restricting sharing of external contact info) run on your device, not ours, and why we ask you to report anything concerning.",
    ],
    [
      "5. Who we share data with",
      "Service providers acting on our instructions only: email delivery (Gmail SMTP, for login codes), payments (Telegram, for Stars purchases), push notifications (your device's push service), object storage for photos (S3-compatible provider). We do not sell your personal data, and we do not share your profile data with advertisers. If a rewarded-ads feature is enabled in the future, it will only use provider-confirmed ad views, never your profile or message data.",
    ],
    [
      "6. How long we keep it",
      "Account and profile data: until you delete your account. Messages: until you or the other participant delete the conversation, or your account is deleted. Payment records: [RETENTION PERIOD — set per your local tax law, typically several years]. Reports and moderation records: retained for a limited period after resolution to handle appeals and repeat-offense patterns. Rate-limiting/security logs: short-lived (days, not months).",
    ],
    [
      "7. Your rights",
      "Depending on your location, you may have the right to: access the personal data we hold about you (Settings → Export my data), correct inaccurate data (Profile → Edit), delete your account and associated data (Settings → Delete account), object to or restrict certain processing, and lodge a complaint with your local data protection authority. We respond to verified requests within the time required by applicable law.",
    ],
    [
      "8. Data export and deletion, in practice",
      "You can download a copy of your data at any time from Settings (\"Export my data\"), which returns your profile, photos, likes, matches, blocks, reports, message metadata, subscriptions, payments, and notification history as a single file. Deleting your account removes these records immediately, except what we are legally required to retain (e.g., payment records).",
    ],
    [
      "9. Children",
      "Respectful Meet is restricted to users 18 and older. We verify date of birth at registration and remove any account later found to belong to a minor.",
    ],
    [
      "10. International transfers",
      "[TO BE FINALIZED — list actual hosting/provider locations and, if data leaves the EU/UK/Switzerland, the transfer mechanism used (e.g., Standard Contractual Clauses).]",
    ],
    [
      "11. Security",
      "We use encrypted transport (HTTPS/WSS) everywhere, hash session tokens and one-time login codes at rest, verify uploaded files rather than trusting their declared type, and rate-limit authentication and messaging endpoints. No system is perfectly secure; if we become aware of a breach affecting your data, we will notify you as required by applicable law.",
    ],
    [
      "12. Changes to this policy",
      "We may update this Privacy Policy from time to time. Material changes will be flagged in-app before they take effect.",
    ],
    [
      "13. Contact and complaints",
      "Questions or requests about your data: [PRIVACY EMAIL]. [EU/UK USERS: name and contact of your EU representative/DPO if required.]",
    ],
  ] as [string, string][],
};

const FR = {
  title: "Politique de confidentialité",
  updated: "Dernière mise à jour : [DATE]",
  sections: [
    [
      "1. Responsable du traitement",
      "[RAISON SOCIALE], immatriculée à [ADRESSE DU SIÈGE], est responsable du traitement des données personnelles décrites ici (« nous »). Contact : [EMAIL VIE PRIVÉE].",
    ],
    [
      "2. Données collectées",
      "Compte : adresse email. Profil : prénom, nom, date de naissance, genre, pays, ville, bio, centres d'intérêt, photos. Activité : likes, matchs, blocages, signalements que vous effectuez. Messages : contenu chiffré de bout en bout (nous stockons l'enveloppe chiffrée, pas le texte lisible) ainsi que des métadonnées (qui, quand, avec qui). Paiements : formule d'abonnement, référence de transaction Telegram, montant — nous ne voyons ni ne stockons les données de carte bancaire. Appareil : jetons de notification push, langue, fuseau horaire, informations sommaires sur la plateforme. Technique : adresse IP de façon transitoire, pour la limitation de débit et la prévention des abus.",
    ],
    [
      "3. Bases légales du traitement",
      "Exécution du service auquel vous avez souscrit (contrat) : compte, mise en relation, messagerie, appels, abonnements. Intérêt légitime : prévention de la fraude et des abus, limitation de débit, journalisation de sécurité. Obligation légale : conservation des données de facturation à des fins comptables/fiscales. Consentement : notifications marketing, désactivables à tout moment dans les Paramètres.",
    ],
    [
      "4. Chiffrement de bout en bout : ce que cela implique pour nous",
      "Les messages textuels sont chiffrés sur votre appareil avant d'atteindre nos serveurs, avec une paire de clés que nous ne voyons jamais. Nous ne pouvons donc réellement pas lire le contenu de vos messages, y compris à des fins de modération — c'est pourquoi certaines protections (comme la restriction du partage de coordonnées externes) s'exécutent sur votre appareil et non sur nos serveurs, et pourquoi nous vous invitons à signaler tout comportement préoccupant.",
    ],
    [
      "5. Partage des données",
      "Uniquement des prestataires agissant sur nos instructions : envoi d'emails (Gmail SMTP, pour les codes de connexion), paiements (Telegram, pour les achats Stars), notifications push (le service push de votre appareil), stockage des photos (prestataire compatible S3). Nous ne vendons pas vos données personnelles et ne partageons pas vos données de profil avec des annonceurs. Si une fonctionnalité de publicité récompensée est activée à l'avenir, elle n'utilisera que des vues publicitaires confirmées par le prestataire, jamais vos données de profil ou de message.",
    ],
    [
      "6. Durées de conservation",
      "Compte et profil : jusqu'à la suppression de votre compte. Messages : jusqu'à suppression de la conversation par vous ou l'autre participant, ou suppression du compte. Données de facturation : [DURÉE — à fixer selon votre législation fiscale locale, généralement plusieurs années]. Signalements et données de modération : conservés une durée limitée après résolution pour traiter les recours et les récidives. Journaux de sécurité/limitation de débit : de courte durée (jours, pas mois).",
    ],
    [
      "7. Vos droits",
      "Selon votre lieu de résidence, vous pouvez disposer des droits suivants : accès aux données vous concernant (Paramètres → Exporter mes données), rectification des données inexactes (Profil → Modifier), suppression de votre compte et des données associées (Paramètres → Supprimer le compte), opposition ou limitation de certains traitements, et réclamation auprès de votre autorité de protection des données. Nous répondons aux demandes vérifiées dans les délais prévus par la loi applicable.",
    ],
    [
      "8. Export et suppression des données, en pratique",
      "Vous pouvez télécharger une copie de vos données à tout moment depuis les Paramètres (« Exporter mes données »), qui renvoie votre profil, vos photos, likes, matchs, blocages, signalements, métadonnées de messages, abonnements, paiements et historique de notifications dans un seul fichier. La suppression du compte efface ces données immédiatement, sauf ce que nous devons conserver légalement (par ex. les données de facturation).",
    ],
    [
      "9. Mineurs",
      "Respectful Meet est réservé aux personnes de 18 ans et plus. La date de naissance est vérifiée à l'inscription et tout compte identifié ultérieurement comme appartenant à un mineur est supprimé.",
    ],
    [
      "10. Transferts internationaux",
      "[À FINALISER — indiquer les localisations réelles d'hébergement/prestataires et, en cas de transfert hors UE/UK/Suisse, le mécanisme utilisé (par ex. clauses contractuelles types).]",
    ],
    [
      "11. Sécurité",
      "Nous utilisons un transport chiffré (HTTPS/WSS) partout, hachons les jetons de session et les codes de connexion à usage unique au repos, vérifions les fichiers téléversés plutôt que de faire confiance à leur type déclaré, et limitons le débit des points d'authentification et de messagerie. Aucun système n'est parfaitement sûr ; en cas de violation de données vous concernant, nous vous en informerons conformément à la loi applicable.",
    ],
    [
      "12. Modifications de cette politique",
      "Nous pouvons mettre à jour cette Politique de confidentialité ponctuellement. Les changements substantiels seront signalés dans l'application avant leur entrée en vigueur.",
    ],
    [
      "13. Contact et réclamations",
      "Questions ou demandes concernant vos données : [EMAIL VIE PRIVÉE]. [UTILISATEURS UE/UK : nom et contact de votre représentant UE/DPO si requis.]",
    ],
  ] as [string, string][],
};

const CONTENT: Record<string, typeof EN> = { EN, FR };

export default function PrivacyPolicy() {
  const { language } = useLanguage();
  const c = CONTENT[language] || EN;
  return (
    <section className="page">
      <SubPageHeader title={c.title} />
      <p style={{ opacity: 0.7, marginTop: 8 }}>{c.updated}</p>
      <div className="stack" style={{ marginTop: 16 }}>
        {c.sections.map(([heading, body]) => (
          <article className="card" key={heading} style={{ padding: 18 }}>
            <h3>{heading}</h3>
            <p style={{ whiteSpace: "pre-line" }}>{body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
