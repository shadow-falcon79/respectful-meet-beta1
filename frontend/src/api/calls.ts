import { getApiBaseUrl } from "./client";
export type CallSignal =
  | { type: "presence"; peer_online: boolean }
  | { type: "peer_joined"; from?: string }
  | { type: "peer_left"; from?: string }
  | { type: "quota_exceeded" }
  | { type: "offer" | "answer" | "ice" | "hangup" | "reject" | "busy"; from?: string; data?: unknown };

function websocketUrl(conversationId: string): string {
  const api = getApiBaseUrl();
  const url = new URL(api, window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/ws/calls/${encodeURIComponent(conversationId)}`;
  return url.toString();
}

export function openCallSocket(conversationId: string): WebSocket {
  return new WebSocket(websocketUrl(conversationId));
}
