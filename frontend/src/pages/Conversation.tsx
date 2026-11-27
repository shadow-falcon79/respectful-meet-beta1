import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Paperclip, Send, MoreHorizontal, ShieldCheck, Phone, Video } from "lucide-react";
import { getConversation, getConversationMessages, sendTextMessage, type ConversationSummary, type Message } from "../api/messaging";
import { ApiError } from "../api/client";
import { getCallQuota } from "../api/ads";
import CallPanel from "../components/CallPanel";
import AdRewardModal from "../components/AdRewardModal";

function formatMessageTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Conversation() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [chat, setChat] = useState<ConversationSummary | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [callMode, setCallMode] = useState<"audio" | "video" | null>(() => { const value = searchParams.get("call"); return value === "audio" || value === "video" ? value : null; });
  const [messageLimitReached, setMessageLimitReached] = useState(false);
  const [showAdModal, setShowAdModal] = useState(false);
  const [callQuotaExhausted, setCallQuotaExhausted] = useState(false);
  const [showCallAdModal, setShowCallAdModal] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function requestCall(mode: "audio" | "video") {
    try {
      const quota = await getCallQuota();
      if (!quota.can_start_call) { setCallQuotaExhausted(true); return; }
      setCallMode(mode);
    } catch {
      // If the quota check itself fails, fall back to letting the call
      // attempt proceed — the server enforces the real limit either way.
      setCallMode(mode);
    }
  }

  useEffect(() => {
    if (!id) return;
    let active = true;
    const load = async () => {
      try {
        const [conversation, nextMessages] = await Promise.all([getConversation(id), getConversationMessages(id)]);
        if (!active) return;
        setChat(conversation);
        setMessages(nextMessages);
        setError(null);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unable to load conversation.");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    const interval = window.setInterval(() => {
      getConversationMessages(id).then((next) => { if (active) setMessages(next); }).catch(() => undefined);
    }, 2500);
    return () => { active = false; window.clearInterval(interval); };
  }, [id]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length]);

  async function handleSend() {
    if (!chat || !draft.trim() || sending) return;
    const text = draft.trim();
    setSending(true);
    try {
      const message = await sendTextMessage(chat.other_user_id, text, chat.id);
      setMessages((prev) => prev.some((item) => item.id === message.id) ? prev : [...prev, { ...message, text }]);
      setDraft("");
      setError(null);
      setMessageLimitReached(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setMessageLimitReached(true);
        setError(null);
      } else {
        setError(err instanceof Error ? err.message : "Message could not be sent.");
      }
    } finally {
      setSending(false);
    }
  }

  if (loading) return <section className="conversation-page"><p className="text-center">Loading…</p></section>;
  if (!chat || error && !messages.length) return <section className="conversation-page"><p className="text-center">{error ?? "Conversation not found."}</p></section>;

  return (
    <div className="conversation-page">
      <header className="conversation-header">
        <button className="icon-btn" onClick={() => navigate("/chats")} aria-label="Back"><ArrowLeft size={19} /></button>
        <button className="conversation-header__profile" onClick={() => navigate(`/profile/view/${chat.id}`)}>
          {chat.other_photo_url ? <img src={chat.other_photo_url} alt={chat.other_first_name} className="conversation-header__avatar" /> : <div className="conversation-header__avatar" />}
          <div className="conversation-header__identity">
            <div className="conversation-header__name">{chat.other_first_name}</div>
            <div className="conversation-header__status">{chat.is_matched ? "Matched" : "Conversation"}</div>
          </div>
        </button>
        <div className="conversation-header__actions"><button className="icon-btn" onClick={() => void requestCall("audio")} aria-label="Start audio call"><Phone size={18} /></button><button className="icon-btn" onClick={() => void requestCall("video")} aria-label="Start video call"><Video size={18} /></button><button className="icon-btn" aria-label="More options"><MoreHorizontal size={20} /></button></div>
      </header>

      <div className="conversation-safety"><ShieldCheck size={14} /> Be respectful. Never share sensitive information.</div>
      {error && <div className="conversation-safety" role="alert">{error === "SECURITY_KEY_CHANGED" ? "Security warning: this contact’s encryption key changed. Messages are blocked until the identity is verified." : error === "CONTENT_NOT_ALLOWED" ? "For your safety, sharing phone numbers, emails, links or external contact handles is not allowed." : error}</div>}
      {messageLimitReached && (
        <div className="conversation-safety" role="alert">
          Free message limit reached for this contact.{" "}
          <button className="link-btn" onClick={() => setShowAdModal(true)} style={{ textDecoration: "underline", fontWeight: 600 }}>
            Watch an ad to unlock 3 more messages
          </button>
        </div>
      )}
      {callQuotaExhausted && (
        <div className="conversation-safety" role="alert">
          You're out of call minutes for today.{" "}
          <button className="link-btn" onClick={() => setShowCallAdModal(true)} style={{ textDecoration: "underline", fontWeight: 600 }}>
            Watch an ad for 10 more minutes
          </button>
        </div>
      )}

      <div className="conversation-messages">
        {messages.map((message) => (
          <div key={message.id} className={`bubble ${message.sender_id === chat.other_user_id ? "bubble--them" : "bubble--me"}`}>
            {message.type === "TEXT" ? <span>{message.text}</span> : <span>{message.type === "PHOTO" ? "📷 Photo" : "🎥 Video"}</span>}
            <span className="bubble__time">{formatMessageTime(message.created_at)}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="conversation-input">
        <button className="icon-btn" aria-label="Attach media" type="button" disabled title="Media upload is coming in the media phase"><Paperclip size={17} /></button>
        <input className="input" maxLength={2000} aria-label={`Message ${chat.other_first_name}`} placeholder={`Message ${chat.other_first_name}…`} value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void handleSend(); } }} disabled={sending} />
        <button className="conversation-send-btn" onClick={() => void handleSend()} aria-label="Send" disabled={sending || !draft.trim()}><Send size={17} /></button>
      </div>
      {callMode && <CallPanel conversationId={chat.id} peerName={chat.other_first_name} mode={callMode} onClose={() => setCallMode(null)} />}
      {showAdModal && (
        <AdRewardModal
          rewardType="unlock_messages"
          conversationId={chat.id}
          onGranted={() => setMessageLimitReached(false)}
          onClose={() => setShowAdModal(false)}
        />
      )}
      {showCallAdModal && (
        <AdRewardModal
          rewardType="extra_call_minutes"
          onGranted={() => setCallQuotaExhausted(false)}
          onClose={() => setShowCallAdModal(false)}
        />
      )}
    </div>
  );
}
