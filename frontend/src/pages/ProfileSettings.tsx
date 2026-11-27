import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Trash2 } from "lucide-react";
import SubPageHeader from "../components/SubPageHeader";
import { useAuth } from "../store/AuthContext";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";
import { deleteMyAccount } from "../api/auth";

const SETTINGS_ITEMS = [
  "Account",
  "Privacy",
  "Notifications",
  "Security",
  "Blocked users",
  "Discovery",
  "Language",
  "Help",
];

// These two navigate straight to the real legal documents rather than the
// one-line placeholder previously rendered by SettingsDetail.
const LEGAL_LINKS: Record<string, string> = {
  Terms: "/legal/terms",
  "Privacy Policy": "/legal/privacy",
};

export default function ProfileSettings() {
  const { language } = useLanguage();
  const t = authTranslations[language];
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  async function handleLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  async function handleDeleteConfirm() {
    await deleteMyAccount();
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <section className="page">
      <SubPageHeader title={t.profileSettings} backTo="/profile" />
      <div className="stack" style={{ marginTop: 16 }}><button className="settings-row" onClick={() => navigate("/guide")}><span>Guide & Help</span><span className="settings-row__meta">›</span></button>
        {SETTINGS_ITEMS.map((item) => (
          <button key={item} className="settings-row" onClick={() => navigate(`/settings/${item.toLowerCase().replace(/ /g, "-")}`)}>
            <span>{item}</span>
            <span className="settings-row__meta">›</span>
          </button>
        ))}
        {Object.entries(LEGAL_LINKS).map(([label, path]) => (
          <button key={label} className="settings-row" onClick={() => navigate(path)}>
            <span>{label}</span>
            <span className="settings-row__meta">›</span>
          </button>
        ))}
        <button className="settings-row" onClick={() => navigate("/privacy/export")}>
          <span>Export my data</span>
          <span className="settings-row__meta">›</span>
        </button>
        <button className="settings-row settings-row--danger" onClick={handleLogout}>
          {t.profileLogout}
        </button>
        <button className="settings-row settings-row--danger" onClick={() => setShowDeleteModal(true)}>
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Trash2 size={16} /> Delete profile
          </span>
        </button>
      </div>

      {showDeleteModal && (
        <div className="modal-backdrop" onClick={() => setShowDeleteModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>Delete your profile?</h2>
            <p style={{ marginBottom: 16 }}>
              This permanently deletes your account and associated profile data. This action cannot be undone.
            </p>
            <div className="stack">
              <button className="btn btn-primary" onClick={handleDeleteConfirm}>
                Delete permanently
              </button>
              <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
