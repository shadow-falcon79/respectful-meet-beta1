import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import SubPageHeader from "../components/SubPageHeader";
import { getConversation, type ConversationSummary } from "../api/messaging";

export default function PublicProfile() {
  const { chatId } = useParams<{ chatId: string }>();
  const [chat, setChat] = useState<ConversationSummary | null | undefined>(undefined);

  useEffect(() => {
    if (!chatId) return;
    getConversation(chatId).then(setChat).catch(() => setChat(null));
  }, [chatId]);

  if (chat === undefined) return <section className="page"><SubPageHeader title="Profile" backTo="/chats" /><p className="text-center">Loading…</p></section>;
  if (!chat) return <section className="page"><SubPageHeader title="Profile" backTo="/chats" /><p className="text-center">Profile not found.</p></section>;

  return (
    <section className="page stack" style={{ gap: 20 }}>
      <SubPageHeader title={chat.other_first_name} backTo={`/chats/${chat.id}`} />
      <div className="profile-header">
        {chat.other_photo_url ? <img src={chat.other_photo_url} alt={chat.other_first_name} className="profile-header__avatar" /> : <div className="profile-header__avatar" />}
        <div className="profile-header__info">
          <h1 style={{ fontSize: "1.3rem" }}>{chat.other_first_name}</h1>
          <p style={{ fontSize: "0.8rem" }}>{chat.is_matched ? "Matched" : "Respectful Meet user"}</p>
        </div>
      </div>
      <div className="card">
        <div className="card-row-header"><h2 style={{ fontSize: "1rem" }}>Conversation</h2></div>
        <p>{chat.is_matched ? "You matched with this person." : "You can chat within the limits of your current plan."}</p>
      </div>
    </section>
  );
}
