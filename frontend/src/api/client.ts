const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export function getApiBaseUrl(): string {
  if (configuredApiBaseUrl) return configuredApiBaseUrl.replace(/\/$/, "");
  if (import.meta.env.PROD) {
    throw new Error("VITE_API_BASE_URL is required for the production frontend");
  }
  return "http://localhost:8000/api/v1";
}

const API_BASE_URL = getApiBaseUrl();

type Lang = "fr" | "en";

function currentLang(): Lang {
  try {
    const value = (localStorage.getItem("rm_language") || navigator.language || "en").toLowerCase();
    return value.startsWith("fr") ? "fr" : "en";
  } catch {
    return "en";
  }
}

const TEXT = {
  network: {
    fr: "Impossible de joindre le serveur. Vérifiez votre connexion internet (Wi-Fi ou données mobiles) puis réessayez.",
    en: "Can't reach the server. Check your internet connection (Wi-Fi or mobile data) and try again.",
  },
  timeout: {
    fr: "Le serveur met trop de temps à répondre (il est peut-être en train de démarrer). Réessayez dans une minute.",
    en: "The server is taking too long to respond (it may be starting up). Try again in a minute.",
  },
  unavailable: {
    fr: "Le serveur est indisponible ou en cours de démarrage. Réessayez dans une minute.",
    en: "The server is unavailable or starting up. Try again in a minute.",
  },
  server: {
    fr: "Erreur du serveur. Ce n'est pas de votre faute : réessayez dans un instant.",
    en: "Server error. It is not your fault: please try again in a moment.",
  },
  tooMany: {
    fr: "Trop de tentatives. Patientez une minute puis réessayez.",
    en: "Too many attempts. Wait a minute and try again.",
  },
  invalid: {
    fr: "Certaines informations sont invalides. Vérifiez le formulaire.",
    en: "Some information is invalid. Please check the form.",
  },
} as const;

// Known backend messages, translated for French users. Unknown ones are shown as-is.
const DETAIL_FR: Record<string, string> = {
  "Invalid username or password": "Nom d'utilisateur ou mot de passe incorrect.",
  "Username already exists": "Ce nom d'utilisateur existe déjà. Choisissez-en un autre.",
  "Passwords do not match": "Les mots de passe ne correspondent pas.",
  "You must be at least 18 years old to register": "Vous devez avoir au moins 18 ans pour vous inscrire.",
  "You must accept the Terms of Service and Privacy Policy to register": "Vous devez accepter les Conditions et la Politique de confidentialité.",
  "Not authenticated": "Veuillez vous connecter.",
  "Session expired or invalid": "Votre session a expiré. Veuillez vous reconnecter.",
  "ACCOUNT_SUSPENDED": "Ce compte est suspendu.",
};

function friendlyMessage(status: number, detail: string): string {
  const lang = currentLang();
  if (status === 0) return TEXT.network[lang];
  if (status === 408) return TEXT.timeout[lang];
  if (status === 429) return TEXT.tooMany[lang];
  if (status === 502 || status === 503 || status === 504) return TEXT.unavailable[lang];
  if (status >= 500) return detail && detail !== "Internal server error" ? `${TEXT.server[lang]} (${detail})` : TEXT.server[lang];
  if (status === 422) return TEXT.invalid[lang];
  if (lang === "fr" && DETAIL_FR[detail]) return DETAIL_FR[detail];
  return detail;
}

/**
 * `message` is what the user sees (clear cause, translated). `detail` keeps the
 * raw backend text and `status` the HTTP status (0 = no connection, 408 = timeout).
 */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(friendlyMessage(status, detail));
    this.status = status;
    this.detail = detail;
  }
}

async function fetchApi(url: string, options: RequestInit, timeoutMs = 60000): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw new ApiError(408, "Request timeout");
    throw new ApiError(0, "Network error"); // browser could not reach the server at all
  } finally {
    window.clearTimeout(timer);
  }
}

async function readJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(502, "Invalid JSON response");
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchApi(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include", // send/receive the HttpOnly session cookie
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, typeof detail === "string" ? detail : "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return readJson<T>(response);
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined });
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body: body === undefined ? undefined : JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetchApi(
    `${API_BASE_URL}${path}`,
    { method: "POST", body: form, credentials: "include" },
    120000,
  );
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail ?? detail; } catch {}
    throw new ApiError(response.status, typeof detail === "string" ? detail : "Upload failed");
  }
  return readJson<T>(response);
}

export interface HealthResponse {
  status: string;
  service: string;
}

export function checkBackendHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
