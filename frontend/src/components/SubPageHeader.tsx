import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function SubPageHeader({ title, backTo }: { title: string; backTo?: string }) {
  const navigate = useNavigate();
  return (
    <header className="subpage-header">
      <button
        className="icon-btn"
        aria-label="Back"
        onClick={() => (backTo ? navigate(backTo) : navigate(-1))}
      >
        <ArrowLeft size={20} />
      </button>
      <h1 style={{ fontSize: "1.15rem" }}>{title}</h1>
    </header>
  );
}
