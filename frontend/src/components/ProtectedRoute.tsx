import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../store/AuthContext";

export default function ProtectedRoute() {
  const { status } = useAuth();

  if (status === "loading") {
    return (
      <div className="app-shell" style={{ alignItems: "center", justifyContent: "center" }}>
        <p>Loading…</p>
      </div>
    );
  }

  if (status === "anonymous") {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
