import { apiGet, apiPut } from "./client";
import { ensureIdentity } from "../services/e2ee";

export interface CryptoIdentity {
  user_id: string;
  public_key_jwk: string;
  fingerprint: string;
  crypto_version: string;
}

export async function registerCryptoIdentity(): Promise<CryptoIdentity> {
  const identity = await ensureIdentity();
  return apiPut<CryptoIdentity>("/crypto/identity", {
    public_key_jwk: JSON.stringify(identity.publicKeyJwk),
    fingerprint: identity.fingerprint,
  });
}

export function getConversationPeerIdentity(conversationId: string): Promise<CryptoIdentity> {
  return apiGet<CryptoIdentity>(`/crypto/conversations/${encodeURIComponent(conversationId)}/peer`);
}
