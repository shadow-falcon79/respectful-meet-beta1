const DB_NAME = "respectful-meet-e2ee";
const STORE = "identity";
const IDENTITY_KEY = "current";
const TRUST_PREFIX = "respectful-meet-e2ee-trust:";
const encoder = new TextEncoder();
const decoder = new TextDecoder();

type StoredIdentity = { privateKey: CryptoKey; publicKeyJwk: JsonWebKey };

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function readIdentity(): Promise<StoredIdentity | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(IDENTITY_KEY);
    req.onsuccess = () => resolve(req.result ?? null);
    req.onerror = () => reject(req.error);
  });
}

async function writeIdentity(identity: StoredIdentity): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(identity, IDENTITY_KEY);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function base64url(bytes: ArrayBuffer): string {
  let binary = "";
  new Uint8Array(bytes).forEach((b) => { binary += String.fromCharCode(b); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64url(value: string): ArrayBuffer {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((value.length + 3) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function stableJson(value: JsonWebKey): string {
  return JSON.stringify({ crv: value.crv, kty: value.kty, x: value.x, y: value.y });
}

export async function fingerprint(publicKeyJwk: JsonWebKey): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(stableJson(publicKeyJwk)));
  const hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0"));
  return hex.join("").match(/.{1,8}/g)?.join(":") ?? "";
}

export async function ensureIdentity(): Promise<{ publicKeyJwk: JsonWebKey; fingerprint: string }> {
  let identity = await readIdentity();
  if (!identity) {
    const pair = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, false, ["deriveBits"]);
    const publicKeyJwk = await crypto.subtle.exportKey("jwk", pair.publicKey);
    identity = { privateKey: pair.privateKey, publicKeyJwk };
    await writeIdentity(identity);
  }
  return { publicKeyJwk: identity.publicKeyJwk, fingerprint: await fingerprint(identity.publicKeyJwk) };
}

async function deriveConversationKey(peerPublicKeyJwk: JsonWebKey): Promise<CryptoKey> {
  const identity = await readIdentity();
  if (!identity) throw new Error("E2EE identity is not initialized");
  const peer = await crypto.subtle.importKey("jwk", peerPublicKeyJwk, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const bits = await crypto.subtle.deriveBits({ name: "ECDH", public: peer }, identity.privateKey, 256);
  return crypto.subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256", salt: encoder.encode("respectful-meet-e2ee-v1"), info: encoder.encode("conversation-message-key") },
    await crypto.subtle.importKey("raw", bits, "HKDF", false, ["deriveKey"]),
    { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"],
  );
}

export async function assertPeerKeyTrusted(conversationId: string, peerFingerprint: string): Promise<void> {
  const key = `${TRUST_PREFIX}${conversationId}`;
  const trusted = localStorage.getItem(key);
  if (!trusted) { localStorage.setItem(key, peerFingerprint); return; }
  if (trusted !== peerFingerprint) throw new Error("SECURITY_KEY_CHANGED");
}

export function localMessageSafetyCheck(text: string): void {
  const normalized = text.replace(/\s+/g, " ").trim();
  const rules = [
    /(?:https?:\/\/|www\.)/i,
    /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i,
    /(?:\+?257|\+?250|\+?243|\+?1)\s*(?:[\d()\-\s]{7,})/,
    /\b(?:whats?app|telegram|signal|instagram|facebook|messenger|snapchat|tiktok|imo|viber|wechat)\b/i,
    /\b(?:whatsapp|telegram|instagram|signal|facebook|messenger|snapchat|tiktok|viber|wechat)\s*[-_ .]*\s*(?:number|num|contact|handle|username|id)?/i,
    /\b(?:give|send|share|drop|add|contact|text|message|find|reach|talk|chat)\b.{0,40}\b(?:me|you|us)\b.{0,50}\b(?:number|phone|email|mail|contact|elsewhere|outside|platform|app|whatsapp|telegram|instagram|signal)\b/i,
  ];
  if (rules.some((rule) => rule.test(normalized))) throw new Error("CONTENT_NOT_ALLOWED");
}

export async function encryptMessage(plaintext: string, peerPublicKeyJwk: JsonWebKey, conversationId: string): Promise<{ ciphertext: string; nonce: string }> {
  const key = await deriveConversationKey(peerPublicKeyJwk);
  const nonceBytes = crypto.getRandomValues(new Uint8Array(12));
  const aad = encoder.encode(`respectful-meet:v1:${conversationId}`);
  const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonceBytes, additionalData: aad }, key, encoder.encode(plaintext));
  return { ciphertext: base64url(encrypted), nonce: base64url(nonceBytes.buffer) };
}

export async function decryptMessage(ciphertext: string, nonce: string, peerPublicKeyJwk: JsonWebKey, conversationId: string): Promise<string> {
  const key = await deriveConversationKey(peerPublicKeyJwk);
  const aad = encoder.encode(`respectful-meet:v1:${conversationId}`);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(fromBase64url(nonce)), additionalData: aad }, key, fromBase64url(ciphertext));
  return decoder.decode(plaintext);
}
