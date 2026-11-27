import { apiDelete, apiGet, apiPatch, uploadFile } from "./client";

export interface ProfilePhoto {
  id: string;
  url: string;
  is_primary: boolean;
  display_order: number;
}

export interface Profile {
  user_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  country: string;
  city: string;
  bio: string | null;
  interests: string[];
  photos: ProfilePhoto[];
}

export function getMyProfile(): Promise<Profile> {
  return apiGet<Profile>("/profiles/me");
}

export function updateMyProfile(payload: Partial<Pick<Profile, "first_name" | "last_name" | "gender" | "country" | "city" | "bio" | "interests">>): Promise<Profile> {
  return apiPatch<Profile>("/profiles/me", payload);
}

export function uploadProfilePhoto(file: File): Promise<ProfilePhoto> {
  return uploadFile<ProfilePhoto>("/profiles/me/photos", file);
}

export function deleteProfilePhoto(photoId: string): Promise<void> {
  return apiDelete<void>(`/profiles/me/photos/${encodeURIComponent(photoId)}`);
}

export function setPrimaryProfilePhoto(photoId: string): Promise<ProfilePhoto> {
  return apiPatch<ProfilePhoto>(`/profiles/me/photos/${encodeURIComponent(photoId)}/primary`, undefined);
}
