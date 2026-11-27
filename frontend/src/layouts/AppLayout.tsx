import { Outlet } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import AppHeader from "../components/AppHeader";

export default function AppLayout() {
  return (
    <div className="app-shell">
      <AppHeader />
      <main className="app-content app-content--with-nav app-content--with-header">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
