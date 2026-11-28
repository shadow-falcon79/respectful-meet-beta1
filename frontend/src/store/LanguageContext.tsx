import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Language = "EN" | "FR" | "ES" | "PT" | "AR" | "DE" | "IT" | "RU" | "ZH" | "JA" | "TR";

export const RTL_LANGUAGES: Language[] = ["AR"];

export const LANGUAGE_META: { code: Language; label: string; browserTags: string[] }[] = [
  { code: "EN", label: "English", browserTags: ["en"] },
  { code: "FR", label: "Français", browserTags: ["fr"] },
  { code: "ES", label: "Español", browserTags: ["es"] },
  { code: "PT", label: "Português", browserTags: ["pt"] },
  { code: "AR", label: "العربية", browserTags: ["ar"] },
  { code: "DE", label: "Deutsch", browserTags: ["de"] },
  { code: "IT", label: "Italiano", browserTags: ["it"] },
  { code: "RU", label: "Русский", browserTags: ["ru"] },
  { code: "ZH", label: "简体中文", browserTags: ["zh"] },
  { code: "JA", label: "日本語", browserTags: ["ja"] },
  { code: "TR", label: "Türkçe", browserTags: ["tr"] },
];

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);
const STORAGE_KEY = "rm_language";

function isSupportedLanguage(value: unknown): value is Language {
  return typeof value === "string" && LANGUAGE_META.some((meta) => meta.code === value);
}

function readSavedLanguage(): Language | null {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return isSupportedLanguage(saved) ? saved : null;
  } catch {
    // Storage can be unavailable in private/restricted browser contexts.
    return null;
  }
}

function detectBrowserLanguage(): Language {
  const navLang = (navigator.language || "en").toLowerCase();
  const match = LANGUAGE_META.find((meta) => meta.browserTags.some((tag) => navLang.startsWith(tag)));
  return match?.code ?? "EN";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => readSavedLanguage() ?? detectBrowserLanguage());
  const isRTL = RTL_LANGUAGES.includes(language);

  useEffect(() => {
    document.documentElement.dir = isRTL ? "rtl" : "ltr";
    document.documentElement.lang = language.toLowerCase();
  }, [language, isRTL]);

  function setLanguage(lang: Language) {
    setLanguageState(isSupportedLanguage(lang) ? lang : "EN");
    try {
      window.localStorage.setItem(STORAGE_KEY, isSupportedLanguage(lang) ? lang : "EN");
    } catch {
      // The language still changes for this session when storage is unavailable.
    }
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, isRTL }}>{children}</LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
