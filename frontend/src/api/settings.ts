import { apiGet, apiPatch } from "./client";
export interface UserSettings {
  language:string; push_notifications:boolean; email_notifications:boolean; marketing_notifications:boolean;
  show_online_status:boolean; profile_discoverable:boolean; show_age:boolean; show_city:boolean;
  min_age:number; max_age:number; discovery_radius_km:number; timezone:string;
}
export const getMySettings = () => apiGet<UserSettings>("/settings/me");
export const updateMySettings = (payload:Partial<UserSettings>) => apiPatch<UserSettings>("/settings/me", payload);
