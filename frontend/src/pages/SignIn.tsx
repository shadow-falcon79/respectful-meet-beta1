import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../layouts/AuthLayout";
import LanguageSelector from "../components/LanguageSelector";
import { signIn, fetchCurrentUser } from "../api/auth";
import { useAuth } from "../store/AuthContext";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

function errorMessage(err: unknown): string {
  return err instanceof Error && err.message ? err.message : "Unable to sign in. Please try again.";
}

export default function SignIn() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn({ username, password });
      const user = await fetchCurrentUser();
      setUser(user);
      navigate("/feed", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <div style={{ position: "absolute", top: 20, right: 20 }}><LanguageSelector /></div>
      <div className="stack" style={{ width: "100%" }}>
        <h1 className="text-center" style={{ fontSize: "1.6rem" }}>Respectful Meet</h1>
        <p className="auth-tagline">{t.tagline}</p>
        <form onSubmit={submit} className="stack">
          <div className="field">
            <label htmlFor="username">{t.username}</label>
            <input id="username" className={`input ${error ? "input-error" : ""}`} value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" autoFocus required />
          </div>
          <div className="field">
            <label htmlFor="password">{t.password}</label>
            <input id="password" type="password" className={`input ${error ? "input-error" : ""}`} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
            {error && <span className="error-text">{error}</span>}
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? t.signingIn : t.signIn}
          </button>
        </form>
        <p className="text-center" style={{ marginTop: 8 }}>
          {t.noAccount} <Link to="/signup">{t.signUp}</Link>
        </p>
      </div>
    </AuthLayout>
  );
}
