import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, ChevronRight, Eye, Pencil, PieChart } from "lucide-react";
import { getMyProfile, type Profile } from "../api/profile";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

function ageFromDob(dob: string) {
  const birth = new Date(`${dob}T00:00:00`);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const beforeBirthday = now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) age--;
  return age;
}

function completion(p: Profile) {
  const fields = [p.first_name, p.last_name, p.date_of_birth, p.gender, p.country, p.city, p.bio, p.interests.length ? "ok" : "", p.photos.length ? "ok" : ""];
  return Math.round(fields.filter(Boolean).length / fields.length * 100);
}

export default function Profile() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { getMyProfile().then(setProfile).catch((e) => setError(e.message)); }, []);
  if (!profile) return <section className="page"><p className="text-center">{error || "Loading…"}</p></section>;
  const primary = profile.photos.find(p => p.is_primary) ?? profile.photos[0];
  const filled = completion(profile);
  return (
    <section className="page stack" style={{ gap: 20 }}>
      <div className="profile-header">
        {primary ? <img src={primary.url} alt={profile.first_name} className="profile-header__avatar" /> : <div className="profile-header__avatar" />}
        <div className="profile-header__info"><h1 style={{ fontSize: "1.3rem" }}>{profile.first_name}, {ageFromDob(profile.date_of_birth)}</h1><p style={{ fontSize: "0.8rem" }}>{profile.city}</p></div>
        <span className="status-pill status-pill--free">☆ Free</span>
      </div>
      <button className="profile-edit-link" onClick={() => navigate("/profile/edit")}>{t.profileEdit} <ChevronRight size={16} /></button>
      <div className="profile-stats">
        <button className="profile-stat" onClick={() => navigate("/profile/photos")}><Camera size={18} /><span className="profile-stat__value">{profile.photos.length}</span><span className="profile-stat__label">{t.profileMedia}</span></button>
        <button className="profile-stat" onClick={() => navigate("/profile/visits")}><Eye size={18} /><span className="profile-stat__value">0</span><span className="profile-stat__label">{t.profileVisits}</span></button>
        <button className="profile-stat" onClick={() => navigate("/profile/completion")}><PieChart size={18} /><span className="profile-stat__value">{filled}%</span><span className="profile-stat__label">{t.profileFilled}</span></button>
      </div>
      <div className="card"><div className="card-row-header"><h2 style={{ fontSize: "1rem" }}>{t.profileAboutYou}</h2><button className="icon-btn icon-btn--sm" onClick={() => navigate("/profile/edit")} aria-label="Edit about you"><Pencil size={14} /></button></div><p>{profile.bio || "Tell people about yourself."}</p></div>
      <div className="card"><div className="card-row-header"><h2 style={{ fontSize: "1rem" }}>{t.profileInterests}</h2><button className="icon-btn icon-btn--sm" onClick={() => navigate("/profile/edit")} aria-label="Edit interests"><Pencil size={14} /></button></div><div className="chip-row chip-row--dark">{profile.interests.map(i => <span key={i} className="chip chip--dark">{i}</span>)}</div></div>
      <div className="card"><div className="card-row-header"><h2 style={{ fontSize: "1rem" }}>{t.profileDetails}</h2></div><div className="chip-row chip-row--dark"><span className="chip chip--dark">{profile.gender}</span><span className="chip chip--dark">{profile.country}</span></div></div>
      <div className="profile-links"><button className="settings-row" onClick={() => navigate("/profile/verify")}><span>{t.profileVerify}</span><span className="settings-row__meta">Not verified ›</span></button><button className="settings-row" onClick={() => navigate("/profile/subscription")}><span>{t.profileSubscription}</span><span className="settings-row__meta">Free ›</span></button><button className="settings-row" onClick={() => navigate("/profile/telegram")}><span>{t.profileTelegram}</span><span className="settings-row__meta">Not connected ›</span></button><button className="settings-row" onClick={() => navigate("/profile/language")}><span>{t.profileLanguage}</span><span className="settings-row__meta">›</span></button><button className="settings-row" onClick={() => navigate("/profile/settings")}><span>{t.profileSettings}</span><span className="settings-row__meta">›</span></button></div>
    </section>
  );
}
