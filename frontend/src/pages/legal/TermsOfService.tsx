import SubPageHeader from "../../components/SubPageHeader";
import { useLanguage } from "../../store/LanguageContext";

/**
 * DRAFT LEGAL TEXT — placeholder company/jurisdiction fields are marked
 * [BRACKETED]. This was written to be structurally complete (the sections a
 * dating app's ToS needs) but has NOT been reviewed by a lawyer and must be
 * before this app accepts real users. In particular: the operating entity
 * name/address, governing law, and dispute-resolution clause need a lawyer
 * licensed in the jurisdiction(s) you actually operate in and sell to.
 */

const EN = {
  title: "Terms of Service",
  updated: "Last updated: [DATE]",
  sections: [
    [
      "1. Who this agreement is with",
      "These Terms of Service (\"Terms\") are a contract between you and [COMPANY LEGAL NAME], a company registered at [REGISTERED ADDRESS] (\"Respectful Meet\", \"we\", \"us\"). By creating an account you agree to these Terms and to our Privacy Policy.",
    ],
    [
      "2. Eligibility",
      "You must be at least 18 years old to create an account. We verify date of birth at registration and remove accounts found to belong to a minor. You confirm that all information you provide is accurate and that you are legally permitted to enter into this agreement in your country of residence.",
    ],
    [
      "3. Your account",
      "You are responsible for the security of your account and for all activity that happens through it. Notify us immediately if you suspect unauthorized access. We use passwordless email sign-in (one-time codes) rather than passwords.",
    ],
    [
      "4. Acceptable use",
      "You agree not to: impersonate another person; harass, threaten, or abuse other users; post content that is illegal, sexually exploitative of minors, or promotes violence; use the service for commercial solicitation, scams, or financial fraud; attempt to circumvent our safety features (including the off-platform contact-sharing restriction); or interfere with the security or operation of the service.",
    ],
    [
      "5. Content you post",
      "You retain ownership of the photos, bio, and other content you upload. You grant us a limited license to host, display, and process that content solely to operate the service (e.g., showing your profile to other users, moderating content). You are responsible for having the rights to anything you upload.",
    ],
    [
      "6. Messages and calls",
      "Text messages are end-to-end encrypted: we cannot read their content and cannot moderate it directly. Because of this, sharing of external contact details is restricted by the app until a conversation is eligible (Premium, or after the conversation has existed for a set number of days), as described in-app. Voice/video calls are signalled through our servers but the media itself is not recorded or stored by us.",
    ],
    [
      "7. Moderation, reporting, and enforcement",
      "You can block or report another user at any time. We may review reports, remove content, and suspend or terminate accounts that violate these Terms, at our discretion and without prior notice for severe violations (e.g., content endangering a minor, threats of violence).",
    ],
    [
      "8. Subscriptions and payments",
      "Premium features are purchased via Telegram Stars. Prices, included features, and refund handling are described at the point of purchase and in our support channels. Purchases are generally non-refundable except where required by law or explicitly offered.",
    ],
    [
      "9. Account deletion",
      "You can delete your account at any time from Settings. Deletion removes your profile, photos, messages, and associated data, subject to what we must legally retain (e.g., payment records for tax/accounting purposes) as described in the Privacy Policy.",
    ],
    [
      "10. Disclaimers",
      "Respectful Meet is a platform for people to meet; we do not perform criminal background checks on users and cannot guarantee the identity, intentions, or conduct of any user. Meet in public places and use your own judgment when meeting someone in person.",
    ],
    [
      "11. Limitation of liability",
      "[TO BE FINALIZED WITH COUNSEL — jurisdiction-specific limitation of liability and disclaimer of warranties clause.]",
    ],
    [
      "12. Changes to these Terms",
      "We may update these Terms from time to time. Material changes will be flagged in-app, and continued use after the effective date constitutes acceptance of the updated Terms.",
    ],
    [
      "13. Governing law and disputes",
      "[TO BE FINALIZED WITH COUNSEL — governing law, venue, and dispute resolution mechanism for your actual operating jurisdiction(s).]",
    ],
    [
      "14. Contact",
      "Questions about these Terms: [SUPPORT EMAIL].",
    ],
  ] as [string, string][],
};

const FR = {
  title: "Conditions d'utilisation",
  updated: "Dernière mise à jour : [DATE]",
  sections: [
    [
      "1. Les parties",
      "Les présentes Conditions d'utilisation (« Conditions ») constituent un contrat entre vous et [RAISON SOCIALE], immatriculée à [ADRESSE DU SIÈGE] (« Respectful Meet », « nous »). En créant un compte, vous acceptez ces Conditions ainsi que notre Politique de confidentialité.",
    ],
    [
      "2. Éligibilité",
      "Vous devez avoir au moins 18 ans pour créer un compte. La date de naissance est vérifiée à l'inscription et tout compte identifié comme appartenant à un mineur est supprimé. Vous confirmez que les informations fournies sont exactes et que vous êtes légalement en mesure de conclure ce contrat dans votre pays de résidence.",
    ],
    [
      "3. Votre compte",
      "Vous êtes responsable de la sécurité de votre compte et de toute activité effectuée via celui-ci. Prévenez-nous immédiatement en cas de suspicion d'accès non autorisé. La connexion se fait sans mot de passe, par code à usage unique envoyé par email.",
    ],
    [
      "4. Utilisation autorisée",
      "Vous vous engagez à ne pas : usurper l'identité d'autrui ; harceler, menacer ou abuser d'autres utilisateurs ; publier du contenu illégal, sexuellement exploitant des mineurs, ou faisant l'apologie de la violence ; utiliser le service à des fins de sollicitation commerciale, d'arnaque ou de fraude financière ; tenter de contourner nos dispositifs de sécurité (y compris la restriction de partage de coordonnées externes) ; ou nuire à la sécurité ou au fonctionnement du service.",
    ],
    [
      "5. Contenu que vous publiez",
      "Vous conservez la propriété des photos, de la bio et de tout autre contenu que vous publiez. Vous nous accordez une licence limitée pour héberger, afficher et traiter ce contenu dans le seul but de faire fonctionner le service (par ex. montrer votre profil à d'autres utilisateurs, modérer le contenu). Vous êtes responsable de détenir les droits sur tout ce que vous publiez.",
    ],
    [
      "6. Messages et appels",
      "Les messages textuels sont chiffrés de bout en bout : nous ne pouvons pas lire leur contenu ni les modérer directement. Pour cette raison, le partage de coordonnées externes est restreint par l'application jusqu'à ce qu'une conversation y soit éligible (abonnement Premium, ou après un certain nombre de jours de conversation), comme indiqué dans l'application. Les appels audio/vidéo transitent par nos serveurs pour la signalisation, mais le contenu audio/vidéo lui-même n'est ni enregistré ni stocké par nos soins.",
    ],
    [
      "7. Modération, signalement et sanctions",
      "Vous pouvez bloquer ou signaler un autre utilisateur à tout moment. Nous pouvons examiner les signalements, retirer du contenu et suspendre ou résilier des comptes qui violent ces Conditions, à notre discrétion et sans préavis en cas de violation grave (par ex. contenu mettant en danger un mineur, menaces de violence).",
    ],
    [
      "8. Abonnements et paiements",
      "Les fonctionnalités Premium s'achètent via Telegram Stars. Les prix, fonctionnalités incluses et modalités de remboursement sont indiqués au moment de l'achat et dans nos canaux d'assistance. Les achats sont en général non remboursables, sauf obligation légale ou offre explicite contraire.",
    ],
    [
      "9. Suppression de compte",
      "Vous pouvez supprimer votre compte à tout moment depuis les Paramètres. La suppression efface votre profil, vos photos, vos messages et les données associées, sous réserve de ce que nous devons conserver légalement (par ex. les données de facturation à des fins comptables/fiscales), comme décrit dans la Politique de confidentialité.",
    ],
    [
      "10. Avertissements",
      "Respectful Meet est une plateforme de mise en relation ; nous n'effectuons pas de vérification d'antécédents judiciaires sur les utilisateurs et ne pouvons garantir l'identité, les intentions ou le comportement d'un utilisateur. Privilégiez les lieux publics et faites preuve de discernement lors d'une rencontre en personne.",
    ],
    [
      "11. Limitation de responsabilité",
      "[À FINALISER AVEC UN AVOCAT — clause de limitation de responsabilité et d'exclusion de garanties propre à votre juridiction.]",
    ],
    [
      "12. Modifications des Conditions",
      "Nous pouvons mettre à jour ces Conditions ponctuellement. Les changements substantiels seront signalés dans l'application ; la poursuite de l'utilisation après la date d'effet vaut acceptation des Conditions mises à jour.",
    ],
    [
      "13. Droit applicable et litiges",
      "[À FINALISER AVEC UN AVOCAT — droit applicable, juridiction compétente et mode de résolution des litiges pour votre ou vos juridictions d'exploitation réelles.]",
    ],
    [
      "14. Contact",
      "Questions sur ces Conditions : [EMAIL DE SUPPORT].",
    ],
  ] as [string, string][],
};

const CONTENT: Record<string, typeof EN> = { EN, FR };

export default function TermsOfService() {
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
