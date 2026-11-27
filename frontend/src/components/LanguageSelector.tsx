import { useLanguage, LANGUAGE_META } from "../store/LanguageContext";

export default function LanguageSelector() {
  const { language, setLanguage } = useLanguage();

  return (
    <select
      className="language-select"
      value={language}
      onChange={(e) => setLanguage(e.target.value as typeof language)}
      aria-label="Language"
    >
      {LANGUAGE_META.map((meta) => (
        <option key={meta.code} value={meta.code}>
          {meta.code}
        </option>
      ))}
    </select>
  );
}
