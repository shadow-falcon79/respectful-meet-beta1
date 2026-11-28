import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../layouts/AuthLayout";
import LanguageSelector from "../components/LanguageSelector";
import DateOfBirthPicker from "../components/DateOfBirthPicker";
import { signUp, fetchCurrentUser, CURRENT_TERMS_VERSION } from "../api/auth";
import { useAuth } from "../store/AuthContext";
import { AVAILABLE_INTERESTS } from "../interests";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

const GENDERS = ["Woman", "Man", "Non-binary"];

export default function SignUp() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [form, setForm] = useState({ username: "", password: "", confirm_password: "", first_name: "", last_name: "", date_of_birth: "", gender: "", country: "", city: "" });
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (key: keyof typeof form, value: string) => setForm((prev) => ({ ...prev, [key]: value }));
  const toggleInterest = (interest: string) => setSelectedInterests((prev) => prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (form.password !== form.confirm_password) { setError(t.passwordMismatch); return; }
    if (!form.date_of_birth) { setError("Veuillez indiquer votre date de naissance."); return; }
    if (!form.gender) { setError("Veuillez choisir votre genre."); return; }
    if (!acceptTerms) { setError(t.termsRequired); return; }
    setLoading(true);
    try {
      await signUp({ ...form, interests: selectedInterests, accept_terms: acceptTerms, terms_version: CURRENT_TERMS_VERSION });
      const user = await fetchCurrentUser();
      setUser(user);
      navigate("/feed", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de créer le compte.");
    } finally { setLoading(false); }
  }

  return (
    <AuthLayout>
      <div style={{ position: "absolute", top: 20, right: 20 }}><LanguageSelector /></div>
      <div className="stack" style={{ width: "100%" }}>
        <h1 className="text-center" style={{ fontSize: "1.6rem" }}>Respectful Meet</h1>
        <p className="auth-tagline">Créer votre compte</p>
        <form onSubmit={submit} className="stack">
          <div className="field"><label htmlFor="username">{t.username}</label><input id="username" className="input" required minLength={2} maxLength={50} value={form.username} onChange={(e) => update("username", e.target.value)} autoComplete="username" /></div>
          <div className="field"><label htmlFor="password">{t.password}</label><input id="password" type="password" className="input" required minLength={8} value={form.password} onChange={(e) => update("password", e.target.value)} autoComplete="new-password" /></div>
          <div className="field"><label htmlFor="confirm_password">{t.confirmPassword}</label><input id="confirm_password" type="password" className="input" required minLength={8} value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} autoComplete="new-password" /></div>
          <div className="field"><label htmlFor="first_name">Prénom</label><input id="first_name" className="input" required value={form.first_name} onChange={(e) => update("first_name", e.target.value)} /></div>
          <div className="field"><label htmlFor="last_name">Nom de famille</label><input id="last_name" className="input" required value={form.last_name} onChange={(e) => update("last_name", e.target.value)} /></div>
          <div className="field"><label>Date de naissance</label><DateOfBirthPicker value={form.date_of_birth} onChange={(v) => update("date_of_birth", v)} /></div>
          <div className="field"><label>Genre</label><div className="interest-picker">{GENDERS.map((g) => <button type="button" key={g} className={`interest-toggle ${form.gender === g ? "active" : ""}`} onClick={() => update("gender", g)}>{g}</button>)}</div></div>
          <div className="field"><label htmlFor="country">Pays</label><input id="country" className="input" required value={form.country} onChange={(e) => update("country", e.target.value)} /></div>
          <div className="field"><label htmlFor="city">Ville</label><input id="city" className="input" required value={form.city} onChange={(e) => update("city", e.target.value)} /></div>
          <div className="field"><label>Centres d'intérêt</label><div className="interest-picker">{AVAILABLE_INTERESTS.map((interest) => <button type="button" key={interest} className={`interest-toggle ${selectedInterests.includes(interest) ? "active" : ""}`} onClick={() => toggleInterest(interest)}>{interest}</button>)}</div></div>
          <label style={{ display: "flex", alignItems: "flex-start", gap: 8, fontWeight: 400 }}><input type="checkbox" checked={acceptTerms} onChange={(e) => setAcceptTerms(e.target.checked)} style={{ marginTop: 3 }} /> <span>J'accepte les <Link to="/legal/terms" target="_blank">Conditions</Link> et la <Link to="/legal/privacy" target="_blank">Politique de confidentialité</Link>.</span></label>
          {error && <span className="error-text">{error}</span>}
          <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t.signingUp : t.signUp}</button>
        </form>
        <p className="text-center" style={{ marginTop: 8 }}>{t.alreadyAccount} <Link to="/signin">{t.signIn}</Link></p>
      </div>
    </AuthLayout>
  );
}
