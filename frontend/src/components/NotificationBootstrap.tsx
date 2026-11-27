import { useEffect } from 'react';
import { useLanguage } from '../store/LanguageContext';
import { getPushPublicKey, notificationHeartbeat, savePushSubscription } from '../api/notifications';

function base64ToBytes(value:string){ const pad='='.repeat((4-value.length%4)%4); const raw=atob((value+pad).replace(/-/g,'+').replace(/_/g,'/')); return Uint8Array.from(raw,c=>c.charCodeAt(0)); }
export default function NotificationBootstrap(){
 const {language}=useLanguage();
 useEffect(()=>{
   let timer: ReturnType<typeof setInterval>|undefined;
   const run=async()=>{
     try{
       if(!('serviceWorker' in navigator)) return;
       const reg=await navigator.serviceWorker.register('/sw.js');
       await notificationHeartbeat();
       timer=setInterval(()=>void notificationHeartbeat(),5*60*1000);
       if(!('Notification' in window)||!('PushManager' in window)) return;
       let permission=Notification.permission;
       if(permission==='default') permission=await Notification.requestPermission();
       if(permission!=='granted') return;
       const {public_key}=await getPushPublicKey();
       if(!public_key) return;
       let sub=await reg.pushManager.getSubscription();
       if(!sub) sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:base64ToBytes(public_key)});
       const json=sub.toJSON();
       if(json.endpoint && json.keys?.p256dh && json.keys?.auth) await savePushSubscription({endpoint:json.endpoint,p256dh:json.keys.p256dh,auth:json.keys.auth,language,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,platform:'web'});
     }catch(e){ console.warn('Push setup unavailable',e); }
   };
   void run(); return()=>{if(timer)clearInterval(timer)};
 },[language]);
 return null;
}
