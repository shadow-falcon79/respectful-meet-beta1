import SubPageHeader from "../components/SubPageHeader";
import { useLanguage, LANGUAGE_META } from "../store/LanguageContext";

export default function ProfileLanguage() {
  const { language, setLanguage } = useLanguage();

  return (
    <section className="page">
      <SubPageHeader title="Language" backTo="/profile" />
      <div className="stack" style={{ marginTop: 16 }}>
        {LANGUAGE_META.map((meta) => (
          <button
            key={meta.code}
            className={`settings-row ${language === meta.code ? "settings-row--active" : ""}`}
            onClick={() => setLanguage(meta.code)}
          >
            <span>{meta.label}</span>
            {language === meta.code && <span>✓</span>}
          </button>
        ))}
      </div>
    </section>
  );
}
