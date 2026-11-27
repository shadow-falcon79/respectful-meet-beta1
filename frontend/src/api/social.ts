import { apiGet, apiPost } from "./client";

export interface FeedProfile {
  user_id: string;
  first_name: string;
  age: number;
  city: string;
  country: string;
  bio: string | null;
  interests: string[];
  photos: string[];
}

export interface LikeResult {
  id: string;
  to_user_id: string;
  matched: boolean;
  created_at: string;
}

export interface Match {
  id: string;
  other_user_id: string;
  other_first_name: string;
  other_photo_url: string | null;
  created_at: string;
}

export function getFeedProfiles(limit = 20): Promise<FeedProfile[]> {
  return apiGet<FeedProfile[]>(`/feed?limit=${limit}`);
}

export function likeProfile(toUserId: string): Promise<LikeResult> {
  return apiPost<LikeResult>("/likes", { to_user_id: toUserId });
}

export function getLikesReceived(): Promise<FeedProfile[]> {
  return apiGet<FeedProfile[]>("/likes/received");
}

export function getMatches(): Promise<Match[]> {
  return apiGet<Match[]>("/matches");
}

export interface LikeUsage {
  used: number;
  limit: number;
  remaining: number;
  premium: boolean;
}

export function getLikeUsage(): Promise<LikeUsage> {
  return apiGet<LikeUsage>("/likes/usage");
}
