import { apiGet, apiPost } from "./client";

export type AdRewardType = "unlock_messages" | "extra_call_minutes";

export interface AdSession {
  session_id: string;
  external_ref: string;
  reward_type: AdRewardType;
  mock_duration_seconds: number | null;
}

export interface AdPostbackResult {
  status: "completed" | "pending" | "expired" | "failed" | "not_found";
  reward_type: AdRewardType | null;
  bonus_messages: number | null;
  bonus_call_minutes: number | null;
}

export function startAdSession(rewardType: AdRewardType, conversationId?: string): Promise<AdSession> {
  return apiPost<AdSession>("/ads/session", { reward_type: rewardType, conversation_id: conversationId ?? null });
}

/** Dev/demo only — simulates the provider's postback until AdMantum (or
 * another offerwall) is approved and wired to POST /ads/postback/{provider}
 * for real. The backend refuses this call outside ads_mock_mode. */
export function confirmMockAdWatched(externalRef: string): Promise<AdPostbackResult> {
  return apiPost<AdPostbackResult>(`/ads/mock/complete?external_ref=${encodeURIComponent(externalRef)}`, {});
}

export interface CallQuota {
  minutes_remaining_today: number;
  can_start_call: boolean;
}

export function getCallQuota(): Promise<CallQuota> {
  return apiGet<CallQuota>("/calls/quota");
}
