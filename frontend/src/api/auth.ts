import { apiDelete, apiGet, apiPost } from "./client";

export interface SignUpPayload {
  username: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  country: string;
  city: string;
  interests: string[];
  accept_terms: boolean;
  terms_version: string;
}

export interface SignInPayload {
  username: string;
  password: string;
}

export interface CurrentUser {
  id: string;
  username: string;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
}

export const CURRENT_TERMS_VERSION = "2026-09-01";

export function signUp(payload: SignUpPayload): Promise<CurrentUser> {
  return apiPost<CurrentUser>("/auth/signup", payload);
}

export function signIn(payload: SignInPayload): Promise<CurrentUser> {
  return apiPost<CurrentUser>("/auth/signin", payload);
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiGet<CurrentUser>("/auth/me");
}

export function logout(): Promise<void> {
  return apiPost<void>("/auth/logout");
}

export function deleteMyAccount(): Promise<void> { return apiDelete<void>("/auth/me"); }
