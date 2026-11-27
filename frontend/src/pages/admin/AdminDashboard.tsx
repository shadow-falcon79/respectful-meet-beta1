import { useEffect, useState } from "react";
import { ArrowUpRight, CreditCard, Heart, MessageCircle, Sparkles, TrendingUp, Users } from "lucide-react";
import { getAdminAnalytics, getAdminReports, getAdminUsers, getAdminVips, getVipCapacity, type AdminAnalytics, type AdminReport, type AdminUser, type VipProfile } from "../../api/admin";

export default function AdminDashboard(){
 const [users,setUsers]=useState<AdminUser[]>([]); const [vips,setVips]=useState<VipProfile[]>([]); const [reports,setReports]=useState<AdminReport[]>([]); const [capacity,setCapacity]=useState({used:0,capacity:500}); const [analytics,setAnalytics]=useState<AdminAnalytics|null>(null); const [error,setError]=useState<string|null>(null);
 useEffect(()=>{Promise.all([getAdminUsers(100),getAdminVips(),getAdminReports(),getVipCapacity(),getAdminAnalytics()]).then(([u,v,r,c,a])=>{setUsers(u);setVips(v);setReports(r);setCapacity(c);setAnalytics(a);}).catch(e=>setError(e instanceof Error?e.message:"Unable to load dashboard."));},[]);
 const active=users.filter(u=>u.is_active&&!u.is_suspended).length; const pending=reports.filter(r=>r.status!=="RESOLVED").length;
 const stats=[
  {label:"Users loaded",value:String(users.length),Icon:Users},
  {label:"Active users (24h)",value:analytics?analytics.active_users_24h.toLocaleString():String(active),Icon:TrendingUp},
  {label:"VIP profiles",value:`${capacity.used}/${capacity.capacity}`,Icon:Sparkles},
  {label:"Pending reports",value:String(pending),Icon:Heart},
  {label:"Matches",value:analytics?analytics.matches_total.toLocaleString():"—",Icon:MessageCircle},
  {label:"Revenue",value:analytics?`${analytics.revenue_stars.toLocaleString()} ⭐`:"—",Icon:CreditCard},
 ];
 return <div className="admin-page"><div className="admin-page-heading"><div><span className="admin-eyebrow">PLATFORM OVERVIEW</span><h2>Admin overview</h2><p>Live data from the current backend. Unavailable metrics are not fabricated.</p></div><a className="admin-primary-btn" href="/admin/users">Manage users <ArrowUpRight size={16}/></a></div>
 {error&&<p role="alert" style={{color:"var(--color-error)"}}>{error}</p>}
 <section className="admin-stat-grid">{stats.map(({label,value,Icon})=><div className="admin-stat" key={label}><div className="admin-stat__top"><span>{label}</span><Icon size={18}/></div><strong>{value}</strong><small>Backend value</small></div>)}</section>
 {analytics&&<section className="admin-mini-cards">
  <div><Sparkles size={20}/><div><strong>{analytics.premium_active.toLocaleString()}</strong><span>Active Premium subscriptions</span></div></div>
  <div><MessageCircle size={20}/><div><strong>{analytics.messages_total.toLocaleString()}</strong><span>Messages sent</span></div></div>
  <div><TrendingUp size={20}/><div><strong>{analytics.call_minutes_total.toLocaleString()}</strong><span>Call minutes logged</span></div></div>
 </section>}
 <section className="admin-grid-two"><div className="admin-panel"><div className="admin-panel__head"><div><h3>VIP capacity</h3><span>Server-authoritative capacity</span></div></div><div style={{padding:20}}><strong>{capacity.used} / {capacity.capacity}</strong><div className="vip-progress" style={{marginTop:12}}><i style={{width:`${Math.min(100,capacity.used/capacity.capacity*100)}%`}}/></div></div></div><div className="admin-panel"><div className="admin-panel__head"><div><h3>Moderation</h3><span>Current reports</span></div></div><div style={{padding:20}}><strong>{pending}</strong><p style={{marginTop:6}}>pending reports</p><a className="admin-text-link" href="/admin/reports">Review reports →</a></div></div></section>
 <section className="admin-panel"><div className="admin-panel__head"><div><h3>Latest users</h3><span>Real accounts returned by the API</span></div><a className="admin-text-link" href="/admin/users">View all →</a></div><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>User</th><th>Country</th><th>Status</th><th>Joined</th><th>Role</th></tr></thead><tbody>{users.slice(0,8).map(u=><tr key={u.id}><td><div className="admin-person"><div><strong>{u.first_name||"Unnamed"}</strong><span>{u.email}</span></div></div></td><td>{u.country||"—"}</td><td><span className={`admin-status ${u.is_suspended?"status-suspended":"status-active"}`}>{u.is_suspended?"Suspended":"Active"}</span></td><td>{new Date(u.created_at).toLocaleDateString()}</td><td>{u.role}</td></tr>)}</tbody></table></div></section>
 <section className="admin-panel"><div className="admin-panel__head"><div><h3>VIP profiles</h3><span>{vips.length} active · capacity {capacity.capacity}</span></div><a className="admin-text-link" href="/admin/vip">Manage VIP profiles →</a></div><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Profile</th><th>Country</th><th>City</th><th>Created</th></tr></thead><tbody>{vips.slice(0,8).map(v=><tr key={v.user_id}><td><div className="admin-person">{v.photo_url?<img src={v.photo_url} alt=""/>:null}<div><strong>{v.first_name}</strong></div></div></td><td>{v.country}</td><td>{v.city}</td><td>{new Date(v.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div></section>
 </div>
}
