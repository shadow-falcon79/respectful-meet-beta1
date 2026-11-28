import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { registerCryptoIdentity } from "../api/crypto";
import { ApiError } from "../api/client";
import {
  fetchCurrentUser,
  logout as apiLogout,
  type CurrentUser,
} from "../api/auth";

// Authentication is backed by the real FastAPI session API.

interface AuthContextValue {
  user: CurrentUser | null;
  status: "loading" | "authenticated" | "anonymous";
  setUser: (user: CurrentUser) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<"loading" | "authenticated" | "anonymous">("loading");

  useEffect(() => {
    let active = true;
    (async () => {
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const currentUser = await fetchCurrentUser();
          if (!active) return;
          setUserState(currentUser);
          setStatus("authenticated");
          return;
        } catch (err) {
          // A real "not logged in" answer (401/403/404...) is final. Network problems,
          // timeouts and 5xx (e.g. the free backend waking up) must NOT log the user out.
          const definitive =
            err instanceof ApiError && err.status >= 400 && err.status < 500 && err.status !== 408 && err.status !== 429;
          if (definitive) break;
          await wait(2000 * (attempt + 1));
          if (!active) return;
        }
      }
      if (active) setStatus("anonymous");
    })();
    return () => { active = false; };
  }, []);

  // Publish the E2EE public key at every session start (boot, sign-in, sign-up),
  // in the background: it must never block the UI, and without it other users
  // cannot open a conversation with this account.
  useEffect(() => {
    if (status !== "authenticated") return;
    registerCryptoIdentity().catch(() => { /* retried at the next session start */ });
  }, [status]);

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
