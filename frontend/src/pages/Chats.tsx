import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getConversations, type ConversationSummary } from "../api/messaging";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

type Filter = "All" | "People";
const FILTERS: Filter[] = ["All", "People"];

function formatTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  if (sameDay) return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function Chats() {
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [chats, setChats] = useState<ConversationSummary[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    getConversations()
      .then((data) => { if (active) setChats(data); })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : "Unable to load conversations."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const visible = useMemo(() => chats
    .filter((c) => filter === "All" || Boolean(c.other_user_id))
    .filter((c) => c.other_first_name.toLowerCase().includes(search.trim().toLowerCase())), [chats, filter, search]);

  return (
    <section className="page">
      <div className="page-sticky-title">
        <h1 style={{ marginBottom: 12 }}>{t.chatsTitle}</h1>
        <input className="input" placeholder={t.chatsSearch} value={search} onChange={(e) => setSearch(e.target.value)} style={{ marginBottom: 12 }} />
        <div className="filter-row" style={{ marginBottom: 0 }}>
          {FILTERS.map((f) => (
            <button key={f} className={`filter-chip ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f === "All" ? t.chatsAll : t.chatsPeople}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-center" style={{ marginTop: 24 }}>{t.feedLoading}</p>}
      {!loading && error && <p className="text-center" style={{ marginTop: 24 }}>{error}</p>}
      {!loading && !error && visible.length === 0 && <p className="text-center" style={{ marginTop: 24 }}>{t.chatsEmpty}</p>}
      <div className="chat-list">
        {visible.map((chat) => (
          <button key={chat.id} className="chat-row" onClick={() => navigate(`/chats/${chat.id}`)}>
            <div className="chat-row__avatar-wrap">
              {chat.other_photo_url ? <img src={chat.other_photo_url} alt={chat.other_first_name} className="chat-row__avatar" /> : <div className="chat-row__avatar" aria-hidden="true" />}
            </div>
            <div className="chat-row__body">
              <div className="chat-row__top">
                <span className="chat-row__name">{chat.other_first_name}</span>
                <span className="chat-row__time">{formatTime(chat.last_message_at)}</span>
              </div>
              <div className="chat-row__bottom">
                <span className="chat-row__last-message">{chat.last_message ?? "Say hello 👋"}</span>
                {chat.unread_count > 0 && <span className="chat-row__unread">{chat.unread_count}</span>}
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
