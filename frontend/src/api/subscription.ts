import { apiGet, apiPost } from "./client";

export interface SubscriptionPlan { plan: string; stars_price: number; duration_days: number; call_minutes_per_day: number; }
export interface SubscriptionStatus { is_premium: boolean; plan: string | null; expires_at: string | null; likes_limit_today: number; likes_used_today: number; }
export const getSubscriptionPlans = () => apiGet<SubscriptionPlan[]>("/subscriptions/plans");
export const getSubscriptionStatus = () => apiGet<SubscriptionStatus>("/subscriptions/me");

export interface CheckoutResponse { payment_id: string; plan: string; stars_amount: number; invoice_url: string; }
export const createCheckout = (plan: string) => apiPost<CheckoutResponse>(`/subscriptions/checkout/${encodeURIComponent(plan)}`);
