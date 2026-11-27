import { CheckCircle2, Circle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import SubPageHeader from "../components/SubPageHeader";

interface ChecklistItem {
  label: string;
  done: boolean;
  to?: string;
}

const CHECKLIST: ChecklistItem[] = [
  { label: "Add at least 3 photos", done: true, to: "/profile/photos" },
  { label: "Write an About you bio", done: false, to: "/profile/edit" },
  { label: "Add your interests", done: true, to: "/profile/edit" },
  { label: "Set your details (height, looking for)", done: true, to: "/profile/edit" },
  { label: "Verify your profile", done: false, to: "/profile/verify" },
  { label: "Connect Telegram", done: false, to: "/profile/telegram" },
];

export default function ProfileCompletion() {
  const navigate = useNavigate();
  const percent = Math.round((CHECKLIST.filter((i) => i.done).length / CHECKLIST.length) * 100);

  return (
    <section className="page">
      <SubPageHeader title="Profile completion" backTo="/profile" />
      <div className="card text-center" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: "1.6rem" }}>{percent}%</h2>
        <p>Complete your profile to get more visibility in the Feed.</p>
      </div>
      <div className="stack">
        {CHECKLIST.map((item) => (
          <button
            key={item.label}
            className="settings-row"
            onClick={() => item.to && navigate(item.to)}
            style={{ color: item.done ? "var(--color-text)" : "var(--color-text-muted)" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {item.done ? (
                <CheckCircle2 size={18} color="var(--color-success)" />
              ) : (
                <Circle size={18} color="var(--color-text-faint)" />
              )}
              {item.label}
            </span>
            <span className="settings-row__meta">›</span>
          </button>
        ))}
      </div>
    </section>
  );
}
