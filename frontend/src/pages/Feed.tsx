import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap, ScanFace, Heart, MessageCircle, X, SlidersHorizontal, MapPin } from "lucide-react";
import type { FeedProfile } from "../api/social";
import { getFeedProfiles, getLikeUsage, likeProfile } from "../api/social";
import { startConversation } from "../api/messaging";
import StoryPhotoCarousel from "../components/StoryPhotoCarousel";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

export default function Feed() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const t = authTranslations[language];
  const [profiles, setProfiles] = useState<FeedProfile[]>([]);
  const [matchToast, setMatchToast] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showDailyLimit, setShowDailyLimit] = useState(false);
  const [dailyRemaining, setDailyRemaining] = useState(0);
  const [isPremium, setIsPremium] = useState(false);
  const [heartBurstProfileId, setHeartBurstProfileId] = useState<string | null>(null);
  const cardRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    Promise.all([getFeedProfiles(), getLikeUsage()])
      .then(([data, usage]) => {
        setProfiles(data);
        setDailyRemaining(usage.remaining);
        setIsPremium(usage.premium);
      })
      .finally(() => setLoading(false));
  }, []);

  function scrollToNext(currentId: string) {
    const index = profiles.findIndex((p) => p.user_id === currentId);
    const next = profiles[index + 1];
    if (next) cardRefs.current[next.user_id]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function consumeLikeAction() {
    if (isPremium || dailyRemaining > 0) return true;
    setShowDailyLimit(true);
    return false;
  }

  async function handleLike(profile: FeedProfile) {
    if (!consumeLikeAction()) return;
    setHeartBurstProfileId(profile.user_id);
    window.setTimeout(() => setHeartBurstProfileId(null), 650);
    try {
      const result = await likeProfile(profile.user_id);
      const usage = await getLikeUsage();
      setDailyRemaining(usage.remaining);
      setIsPremium(usage.premium);
    window.setTimeout(() => scrollToNext(profile.user_id), 220);
      if (result.matched) {
        setMatchToast(true);
        window.setTimeout(() => setMatchToast(false), 1800);
      }
      setProfiles((current) => current.filter((item) => item.user_id !== profile.user_id));
    } catch (error) {
      console.error(error);
      const usage = await getLikeUsage().catch(() => null);
      if (usage) { setDailyRemaining(usage.remaining); setIsPremium(usage.premium); }
    }
  }

  async function handleDislike(profile: FeedProfile) {
    setProfiles((current) => current.filter((item) => item.user_id !== profile.user_id));
  }

  async function handleMessage(profile: FeedProfile) {
    try {
      const conversation = await startConversation(profile.user_id);
      navigate(`/chats/${conversation.id}`);
    } catch (error) {
      console.error(error);
    }
  }

  if (loading) return <section className="feed-loading">{t.feedLoading}</section>;

  return (
    <div className="feed-page">
      <header className="feed-topbar" aria-label="Feed header">
        <span className="feed-pill feed-pill--accent">{t.feedProfiles}</span>
        <div className="feed-header-actions">
          <span className="feed-remaining" aria-label={`${dailyRemaining} likes remaining today`}>{isPremium ? "Premium" : `${dailyRemaining} likes today`}</span>
          <button className="feed-pill" onClick={() => setShowFilters(true)} aria-label="Open filters">
            <SlidersHorizontal size={16} /> {t.feedFilters}
          </button>
        </div>
      </header>

      {matchToast && <div className="match-toast" role="status">✨ It's a match!</div>}

      <main className="feed-scroll">
        {profiles.map((profile) => (
          <article key={profile.user_id} className="feed-card" ref={(el) => { cardRefs.current[profile.user_id] = el; }}>
            <div className="feed-card__photo">
              <StoryPhotoCarousel photos={profile.photos} />
              <div className="feed-card__scrim" aria-hidden="true" />

              <div className="feed-action-rail">
                <button className="feed-rail-btn" aria-label="Boost"><Zap size={19} /></button>
                <button className="feed-rail-btn" aria-label="View profile details"><ScanFace size={19} /></button>
                <div className="feed-like-wrap">
                  {heartBurstProfileId === profile.user_id && <div className="heart-burst" aria-hidden="true"><span>♥</span><span>♥</span><span>♥</span><span>✦</span><span>♥</span><span>✦</span></div>}
                  <button className="feed-rail-btn feed-rail-btn--like" aria-label={`Like ${profile.first_name}`} onClick={() => handleLike(profile)}>
                    <Heart size={23} fill="currentColor" />
                  </button>
                </div>
                <button className="feed-rail-btn" aria-label={`Message ${profile.first_name}`} onClick={() => void handleMessage(profile)}><MessageCircle size={19} /></button>
                <button className="feed-rail-btn" aria-label="Pass" onClick={() => handleDislike(profile)}><X size={19} /></button>
              </div>

              <div className="feed-card__info">
                <div className="feed-card__identity">
                  <h2 className="feed-card__name">{profile.first_name}, {profile.age}</h2>
                  <p className="feed-card__meta"><MapPin size={13} /> {profile.city} · {"—"} cm · {"—"} kg</p>
                </div>
                <div className="chip-row">
                  {profile.interests.map((interest, index) => (
                    <span key={interest} className={`chip ${index === 0 ? "chip--primary" : ""}`}>{interest}</span>
                  ))}
                </div>
              </div>
            </div>
          </article>
        ))}
        {profiles.length === 0 && <div className="feed-empty"><h1>That's everyone for now</h1><p>Come back later for new profiles.</p></div>}
      </main>

      {showDailyLimit && (
        <div className="modal-backdrop" onClick={() => setShowDailyLimit(false)}>
          <div className="modal-card daily-limit-modal" role="dialog" aria-modal="true" aria-labelledby="daily-limit-title" onClick={(event) => event.stopPropagation()}>
            <div className="daily-limit-modal__icon">♥</div>
            <h2 id="daily-limit-title">{t.feedEndTitle}</h2>
            <p>{t.feedEndSubtitle}</p>
            <div className="daily-limit-modal__actions">
              <button className="btn btn-primary" onClick={() => { setShowDailyLimit(false); navigate("/profile/subscription"); }}>{t.feedUpgrade}</button>
              <button className="btn btn-ghost" onClick={() => setShowDailyLimit(false)}>{t.gotIt}</button>
            </div>
          </div>
        </div>
      )}

      {showFilters && (
        <div className="modal-backdrop" onClick={() => setShowFilters(false)}>
          <div className="modal-card filter-modal" role="dialog" aria-modal="true" aria-labelledby="filter-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-card__header"><div><span className="modal-eyebrow">DISCOVER</span><h2 id="filter-title">{t.feedFilters}</h2></div><button className="modal-close" onClick={() => setShowFilters(false)} aria-label="Close filters">×</button></div>
            <div className="filter-demo-grid">
              <div><span>Age</span><strong>22 — 35</strong></div>
              <div><span>Distance</span><strong>50 km</strong></div>
              <div><span>Interests</span><strong>Any</strong></div>
              <div><span>Country</span><strong>Any</strong></div>
            </div>
            <p className="modal-note">Advanced filters are not enabled yet and will not be simulated.</p>
            <button className="btn btn-primary" onClick={() => setShowFilters(false)}>Apply filters</button>
          </div>
        </div>
      )}
    </div>
  );
}
