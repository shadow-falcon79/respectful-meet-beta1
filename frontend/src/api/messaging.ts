import { apiGet, apiPost } from "./client";
import { assertPeerKeyTrusted, encryptMessage, decryptMessage, ensureIdentity, localMessageSafetyCheck } from "../services/e2ee";
import { getConversationPeerIdentity } from "./crypto";

export interface ConversationSummary {
  id: string; other_user_id: string; other_first_name: string; other_photo_url: string | null;
  is_matched: boolean; last_message: string | null; last_message_at: string | null; unread_count: number;
}
export type MessageType = "TEXT" | "PHOTO" | "VIDEO";
export interface Message {
  id: string; conversation_id: string; sender_id: string; type: MessageType;
  text: string | null; ciphertext: string | null; nonce: string | null; sender_public_key_jwk: string | null;
  crypto_version: string; media_url: string | null; is_read: boolean; created_at: string;
}
export function getConversations(): Promise<ConversationSummary[]> { return apiGet("/conversations"); }
export function getConversation(id: string): Promise<ConversationSummary> { return apiGet(`/conversations/${encodeURIComponent(id)}`); }
export function startConversation(toUserId: string): Promise<ConversationSummary> { return apiPost("/conversations", { to_user_id: toUserId }); }
export interface ExternalSharingStatus { allowed: boolean; reason: string; unlock_at: string; }
export function getExternalSharingStatus(conversationId: string): Promise<ExternalSharingStatus> { return apiGet(`/conversations/${encodeURIComponent(conversationId)}/external-sharing`); }

export async function getConversationMessages(conversationId: string, limit = 50): Promise<Message[]> {
  const messages = await apiGet<Message[]>(`/conversations/${encodeURIComponent(conversationId)}/messages?limit=${limit}`);
  const peer = await getConversationPeerIdentity(conversationId);
  await assertPeerKeyTrusted(conversationId, peer.fingerprint);
  const peerJwk = JSON.parse(peer.public_key_jwk) as JsonWebKey;
  const own = await ensureIdentity();
  const ownJwk = own.publicKeyJwk;
  return Promise.all(messages.map(async (message) => {
    if (message.type !== "TEXT" || !message.ciphertext || !message.nonce) return message;
    try {
      const senderKey = message.sender_public_key_jwk
        ? JSON.parse(message.sender_public_key_jwk) as JsonWebKey
        : peerJwk;
      const expectedSenderKey = message.sender_id === peer.user_id ? peerJwk : ownJwk;
      if (JSON.stringify(senderKey) !== JSON.stringify(expectedSenderKey)) {
        return { ...message, text: "Security warning: sender key changed." };
      }
      // ECDH decryption must use the OTHER participant's public key. Both
      // directions derive the same shared secret: my private key + peer public
      // key. Using the sender's key for self-authored messages derives the
      // wrong secret and made sent messages fail after a refresh.
      return { ...message, text: await decryptMessage(message.ciphertext, message.nonce, peerJwk, conversationId) };
    } catch {
      return { ...message, text: "Unable to decrypt this message." };
    }
  }));
}

export async function sendTextMessage(toUserId: string, text: string, conversationId: string): Promise<Message> {
  const sharing = await getExternalSharingStatus(conversationId);
  if (!sharing.allowed) localMessageSafetyCheck(text);
  const peer = await getConversationPeerIdentity(conversationId);
  await assertPeerKeyTrusted(conversationId, peer.fingerprint);
  const identity = await ensureIdentity();
  const encrypted = await encryptMessage(text, JSON.parse(peer.public_key_jwk) as JsonWebKey, conversationId);
  return apiPost<Message>("/messages", {
    to_user_id: toUserId,
    ciphertext: encrypted.ciphertext,
    nonce: encrypted.nonce,
    sender_public_key_jwk: JSON.stringify(identity.publicKeyJwk),
    crypto_version: "v1",
  });
}
