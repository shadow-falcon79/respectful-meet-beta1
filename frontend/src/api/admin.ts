import { apiDelete, apiGet, apiPatch, apiPost, getApiBaseUrl } from "./client";

export interface AdminUser {
  id: string; email: string; first_name: string | null; country: string | null;
  is_active: boolean; is_suspended: boolean; role: string; created_at: string;
}
export interface VipProfile {
  user_id: string; first_name: string; country: string; city: string;
  photo_url: string | null; created_at: string;
}
export interface VipCapacity { used: number; capacity: number; available: number; }
export interface AdminReport { id: string; reported_user_id: string; reason: string; status: string; created_at: string; }

export const getAdminUsers = (limit = 100) => apiGet<AdminUser[]>(`/admin/users?limit=${limit}`);
export const suspendAdminUser = (id: string) => apiPost<void>(`/admin/users/${encodeURIComponent(id)}/suspend`);
export const unsuspendAdminUser = (id: string) => apiPost<void>(`/admin/users/${encodeURIComponent(id)}/unsuspend`);
export const deleteAdminUser = (id: string) => apiDelete<void>(`/admin/users/${encodeURIComponent(id)}`);
export const getVipCapacity = () => apiGet<VipCapacity>("/admin/vip/capacity");
export const getAdminVips = () => apiGet<VipProfile[]>("/admin/vip");
export const deleteAdminVip = (id: string) => apiDelete<void>(`/admin/vip/${encodeURIComponent(id)}`);
export const getAdminReports = () => apiGet<AdminReport[]>("/admin/reports");
export const resolveAdminReport = (id: string) => apiPost<AdminReport>(`/admin/reports/${encodeURIComponent(id)}/resolve`);

export interface VipCreatePayload {
  first_name: string; last_name: string; date_of_birth: string; gender: string;
  country: string; city: string; bio?: string; interests?: string[];
}
export function createAdminVip(payload: VipCreatePayload, file: File): Promise<VipProfile> {
  const form = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    form.append(key, Array.isArray(value) ? JSON.stringify(value) : String(value ?? ""));
  });
  form.append("file", file);
  return fetchWithForm<VipProfile>("/admin/vip", form);
}

async function fetchWithForm<T>(path: string, body: FormData): Promise<T> {
  const base = getApiBaseUrl();
  const response = await fetch(`${base}${path}`, { method: "POST", body, credentials: "include" });
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail ?? detail; } catch {}
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export interface AdminPayment { id: string; user_id: string; plan: string; stars_amount: number; status: string; telegram_user_id: string | null; telegram_charge_id: string | null; created_at: string; }
export const getAdminPayments = (limit = 100) => apiGet<AdminPayment[]>(`/admin/payments?limit=${limit}`);
export const refundAdminPayment = (id: string) => apiPost<AdminPayment>(`/admin/payments/${encodeURIComponent(id)}/refund`);


export interface AdminLikeMatchStats { total_likes:number; likes_today:number; total_matches:number; matches_today:number; match_rate_percent:number; }
export interface AdminMessageStats { total_messages:number; messages_today:number; total_conversations:number; active_conversations_24h:number; }
export interface AdminMessageMetadata { conversation_id:string; participant_a_id:string; participant_b_id:string; message_count:number; last_message_at:string|null; last_message_type:string|null; }
export interface AdminAnalytics { users_total:number; users_today:number; active_users_24h:number; likes_total:number; matches_total:number; messages_total:number; conversations_total:number; premium_active:number; payments_successful:number; revenue_stars:number; calls_total:number; call_minutes_total:number; }
export interface AdminSubscription { id:string; user_id:string; plan:string; status:string; started_at:string; expires_at:string; payment_id:string|null; }
export interface AdminSetting { key:string; value:string; editable:boolean; description:string; }

export const getAdminLikeStats = () => apiGet<AdminLikeMatchStats>("/admin/likes");
export const getAdminMessageStats = () => apiGet<AdminMessageStats>("/admin/messages");
export const getAdminMessageMetadata = (limit=100) => apiGet<AdminMessageMetadata[]>(`/admin/messages/metadata?limit=${limit}`);
export const getAdminAnalytics = () => apiGet<AdminAnalytics>("/admin/analytics");
export const getAdminSubscriptions = (limit=100) => apiGet<AdminSubscription[]>(`/admin/subscriptions?limit=${limit}`);
export const getAdminSettings = () => apiGet<AdminSetting[]>("/admin/settings");
export const updateAdminSetting = (key:string, value:boolean|string) => apiPatch<AdminSetting>(`/admin/settings/${encodeURIComponent(key)}`, {value});
