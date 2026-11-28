import { useEffect, useRef, useState } from "react";
import { Phone, Video, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../store/AuthContext";
import { getApiBaseUrl } from "../api/client";

function inboxUrl(): string {
  const api = getApiBaseUrl();
  const url = new URL(api, window.location.origin); url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/ws/call-inbox`; return url.toString();
}

export default function IncomingCallListener() {
  const socketRef = useRef<WebSocket | null>(null);
  const navigate = useNavigate();
  const { status } = useAuth();
  const [call, setCall] = useState<{ conversationId: string; mode: "audio" | "video" } | null>(null);
  useEffect(() => {
    if (status !== "authenticated") { socketRef.current?.close(); socketRef.current = null; setCall(null); return; }
    let stopped = false;
    let attempts = 0;
    let timer: number | undefined;
    const connect = () => {
      if (stopped) return;
      let opened = false;
      let socket: WebSocket;
      try { socket = new WebSocket(inboxUrl()); } catch { return; }
      socketRef.current = socket;
      socket.onopen = () => { opened = true; attempts = 0; };
      socket.onmessage = (event) => { try { const m = JSON.parse(event.data); if (m.type === "incoming_call") setCall({ conversationId: m.conversation_id, mode: m.mode === "video" ? "video" : "audio" }); } catch { /* ignore malformed signalling */ } };
      socket.onclose = () => {
        if (stopped) return;
        attempts += 1;
        // Never connected (e.g. WebSocket not proxied, backend asleep): back off, then give up
        // instead of hammering the backend every 1.5s forever.
        if (!opened && attempts >= 5) return;
        timer = window.setTimeout(connect, Math.min(1500 * 2 ** attempts, 60000));
      };
    };
    connect();
    return () => { stopped = true; window.clearTimeout(timer); socketRef.current?.close(); socketRef.current = null; };
  }, [status]);
  if (!call) return null;
  return <div className="incoming-call" role="alert"><div><strong>Incoming {call.mode} call</strong><span>Someone wants to call you</span></div><button className="call-control" onClick={() => navigate(`/chats/${call.conversationId}?call=${call.mode}`)} aria-label="Answer"><Phone size={18}/></button><button className="call-control is-off" onClick={() => setCall(null)} aria-label="Decline"><X size={18}/></button>{call.mode === "video" && <Video size={16}/>}</div>;
}
