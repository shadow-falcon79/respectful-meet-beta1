import { apiGet, apiPost } from './client';
export interface NotificationItem { id:string; type:string; title:string; body:string|null; is_read:boolean; created_at:string; }
export function getNotifications():Promise<NotificationItem[]> { return apiGet('/notifications'); }
export function getNotificationStats():Promise<{unread:number;total:number}> { return apiGet('/notifications/stats'); }
export function markNotificationRead(id:string):Promise<void> { return apiPost(`/notifications/${encodeURIComponent(id)}/read`); }
export function markAllNotificationsRead():Promise<void> { return apiPost('/notifications/read-all'); }
export function getPushPublicKey():Promise<{public_key:string}> { return apiGet('/notifications/push/public-key'); }
export function savePushSubscription(body:unknown):Promise<void> { return apiPost('/notifications/push/subscribe',body); }
export function notificationHeartbeat():Promise<void> { return apiPost('/notifications/heartbeat'); }
