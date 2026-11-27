import { NavLink } from "react-router-dom";
import { Compass, Heart, MessageCircle, User } from "lucide-react";
import { getLikesReceived } from "../api/social";
import { useEffect, useState } from "react";
import { useLanguage } from "../store/LanguageContext";
import { authTranslations } from "../i18n/translations";

export default function BottomNav() {
  const { language } = useLanguage();
  const [badge, setBadge] = useState(0);
  useEffect(() => { let active = true; getLikesReceived().then((items) => { if (active) setBadge(items.length); }).catch(() => undefined); return () => { active = false; }; }, []);
  const t = authTranslations[language];

  const TABS = [
    { to: "/feed", label: t.navFeed, Icon: Compass },
    { to: "/likes", label: t.navLikes, Icon: Heart, badge },
    { to: "/chats", label: t.navChats, Icon: MessageCircle },
    { to: "/profile", label: t.navProfile, Icon: User },
  ];

  return (
    <nav className="bottom-nav">
      {TABS.map(({ to, label, Icon, badge }) => (
        <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : "")}>
          {({ isActive }) => (
            <>
              <span className="bottom-nav__icon-wrap">
                <Icon
                  size={22}
                  strokeWidth={isActive ? 2.2 : 1.8}
                  fill={isActive && Icon === Heart ? "currentColor" : "none"}
                />
                {!!badge && <span className="bottom-nav__badge">{badge}</span>}
              </span>
              <span>{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
