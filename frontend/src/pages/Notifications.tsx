import { useEffect, useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import SubPageHeader from '../components/SubPageHeader';
import { getNotifications, markAllNotificationsRead, markNotificationRead, type NotificationItem } from '../api/notifications';
export default function Notifications(){
 const [items,setItems]=useState<NotificationItem[]>([]);
 const load=()=>getNotifications().then(setItems).catch(()=>{});
 useEffect(()=>{void load()},[]);
 async function read(id:string){await markNotificationRead(id);setItems(x=>x.map(n=>n.id===id?{...n,is_read:true}:n));}
 async function readAll(){await markAllNotificationsRead();setItems(x=>x.map(n=>({...n,is_read:true})));}
 return <section className="page"><SubPageHeader title="Notifications" backTo="/feed"/><div style={{display:'flex',justifyContent:'flex-end',margin:'12px 0'}}><button className="btn btn-ghost" onClick={()=>void readAll()}><CheckCheck size={16}/> Mark all read</button></div><div className="stack">{items.length===0?<div className="card" style={{padding:20,textAlign:'center'}}><Bell size={26}/><p>No notifications yet.</p></div>:items.map(n=><button key={n.id} onClick={()=>void read(n.id)} className="card" style={{textAlign:'left',padding:16,border:n.is_read?'1px solid #eee':'1px solid #bbb',background:n.is_read?'white':'#fafafa'}}><strong>{n.title}</strong><p style={{margin:'5px 0'}}>{n.body}</p><small>{new Date(n.created_at).toLocaleString()}</small></button>)}</div></section>
}
