import { Bell } from "lucide-react";
import { Link } from "react-router-dom";
import Logo from "./Logo";
export default function AppHeader(){return <header className="app-header"><Logo variant="icon" height={26}/><span className="app-header__name">Respectful Meet</span><Link to="/notifications" aria-label="Notifications" style={{marginLeft:'auto'}}><Bell size={21}/></Link></header>}
