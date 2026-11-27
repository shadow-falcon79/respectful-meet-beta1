import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getLikesReceived, getMatches, type FeedProfile, type Match } from "../api/social";
import { startConversation } from "../api/messaging";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

type Tab = "liked" | "matches";

export default function Likes() {
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [tab, setTab] = useState<Tab>("liked");
  const [likedYou, setLikedYou] = useState<FeedProfile[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getLikesReceived(), getMatches()])
      .then(([likes, matchData]) => { setLikedYou(likes); setMatches(matchData); })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load likes."))
      .finally(() => setLoading(false));
  }, []);

  async function openChat(userId: string) {
    try {
      const conversation = await startConversation(userId);
      navigate(`/chats/${conversation.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open conversation.");
    }
  }

  return (
    <section className="page">
      <div className="page-sticky-title">
        <h1 style={{ marginBottom: 12 }}>{t.likesTitle}</h1>
        <div className="segmented">
          <button className={tab === "liked" ? "active" : ""} onClick={() => setTab("liked")}>{t.likesLikedYou}</button>
          <button className={tab === "matches" ? "active" : ""} onClick={() => setTab("matches")}>{t.likesMatches}</button>
        </div>
      </div>
      {loading && <p className="text-center" style={{ marginTop: 24 }}>{t.feedLoading}</p>}
      {error && <p className="text-center" style={{ marginTop: 24 }} role="alert">{error}</p>}

      {!loading && !error && tab === "liked" && (
        <div className="liked-grid">
          {likedYou.length === 0 && <p className="text-center" style={{ gridColumn: "1 / -1" }}>No likes yet.</p>}
          {likedYou.map((profile) => (
            <button key={profile.user_id} className="liked-tile" style={{ backgroundImage: profile.photos[0] ? `url(${profile.photos[0]})` : undefined }} onClick={() => void openChat(profile.user_id)} aria-label={`Open chat with ${profile.first_name}`} />
          ))}
        </div>
      )}

      {!loading && !error && tab === "matches" && (
        <div className="stack" style={{ marginTop: 16 }}>
          {matches.length === 0 && <p className="text-center">No matches yet — keep swiping in the Feed!</p>}
          {matches.map((match) => (
            <button key={match.id} className="match-row" onClick={() => void openChat(match.other_user_id)}>
              {match.other_photo_url ? <img src={match.other_photo_url} alt={match.other_first_name} className="match-row__avatar" /> : <div className="match-row__avatar" />}
              <div className="match-row__info"><span className="match-row__name">{match.other_first_name}</span><span className="match-row__status">Matched</span></div>
              <span className="match-row__cta">💬</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
