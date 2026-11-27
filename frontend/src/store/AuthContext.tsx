import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { registerCryptoIdentity } from "../api/crypto";
import {
  fetchCurrentUser,
  logout as apiLogout,
  type CurrentUser,
} from "../api/auth";

// Authentication is now backed by the real FastAPI session API. The validated
// UI remains unchanged; only the data source has been switched.

interface AuthContextValue {
  user: CurrentUser | null;
  status: "loading" | "authenticated" | "anonymous";
  setUser: (user: CurrentUser) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<"loading" | "authenticated" | "anonymous">("loading");

  useEffect(() => {
    let active = true;
    fetchCurrentUser()
      .then(async (currentUser) => {
        if (!active) return;
        setUserState(currentUser);
        try { await registerCryptoIdentity(); } catch { /* identity can be retried on the next authenticated boot */ }
        if (active) setStatus("authenticated");
      })
      .catch(() => { if (active) setStatus("anonymous"); });
    return () => { active = false; };
  }, []);

  const setUser = useCallback((currentUser: CurrentUser) => {
    setUserState(currentUser);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUserState(null);
    setStatus("anonymous");
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, setUser, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
