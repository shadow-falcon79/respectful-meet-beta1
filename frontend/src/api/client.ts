const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export function getApiBaseUrl(): string {
  if (configuredApiBaseUrl) return configuredApiBaseUrl.replace(/\/$/, "");
  if (import.meta.env.PROD) {
    throw new Error("VITE_API_BASE_URL is required for the production frontend");
  }
  return "http://localhost:8000/api/v1";
}

const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: form,
    credentials: "include",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail ?? detail; } catch {}
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export function checkBackendHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
