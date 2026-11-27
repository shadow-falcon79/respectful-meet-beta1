import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
import { BarChart3, Bell, CreditCard, Flag, Heart, LayoutDashboard, Menu, MessageCircle, Settings, Shield, Sparkles, UserRound, Users, X } from "lucide-react";
import Logo from "../components/Logo";

const NAV = [
 {to:"/admin",label:"Overview",Icon:LayoutDashboard}, {to:"/admin/users",label:"Users",Icon:Users}, {to:"/admin/profiles",label:"Profiles",Icon:UserRound}, {to:"/admin/vip",label:"VIP Profiles",Icon:Sparkles}, {to:"/admin/likes",label:"Likes & Matches",Icon:Heart}, {to:"/admin/messages",label:"Messages",Icon:MessageCircle}, {to:"/admin/reports",label:"Reports & Moderation",Icon:Flag}, {to:"/admin/subscriptions",label:"Subscriptions",Icon:Shield}, {to:"/admin/payments",label:"Payments",Icon:CreditCard}, {to:"/admin/notifications",label:"Notifications",Icon:Bell}, {to:"/admin/analytics",label:"Analytics",Icon:BarChart3}, {to:"/admin/settings",label:"Settings",Icon:Settings},
];
export default function AdminLayout(){
 const [open,setOpen]=useState(false); const location=useLocation();
 const title=location.pathname==="/admin"?"Overview":NAV.find(n=>location.pathname.startsWith(n.to))?.label||"Admin";
 return <div className="admin-shell">
  <aside className={`admin-sidebar ${open?"is-open":""}`}><div className="admin-brand"><div className="admin-brand__mark"><Logo variant="icon" height={22} /></div><div><strong>Respectful Meet</strong><span>Admin Console</span></div><button className="admin-mobile-close" onClick={()=>setOpen(false)}><X size={20}/></button></div>
   <nav className="admin-nav">{NAV.map(({to,label,Icon})=><NavLink key={to} to={to} end={to==="/admin"} onClick={()=>setOpen(false)} className={({isActive})=>isActive?"active":""}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
   <div className="admin-sidebar-footer"><Shield size={16}/><span>Beta administration</span></div>
  </aside>
  {open&&<button className="admin-overlay" aria-label="Close menu" onClick={()=>setOpen(false)}/>} 
  <div className="admin-main"><header className="admin-header"><button className="admin-menu-btn" onClick={()=>setOpen(true)} aria-label="Open admin menu"><Menu size={21}/></button><div><span className="admin-breadcrumb">Admin /</span><h1>{title}</h1></div><div className="admin-header-actions"><button className="admin-icon-btn" aria-label="Notifications"><Bell size={18}/><i/></button><div className="admin-avatar">AD</div><div className="admin-account"><strong>Admin</strong><span>Administrator</span></div></div></header><main className="admin-content"><Outlet/></main></div>
 </div>
}
