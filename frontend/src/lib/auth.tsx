import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api, tokenStore } from "./api";
import type { Me, TokenPair } from "./types";

interface AuthContextValue {
  user: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<Me>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    if (!tokenStore.access) {
      setUser(null);
      return;
    }
    try {
      const me = await api<Me>("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string): Promise<Me> => {
    const tokens = await api<TokenPair>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    tokenStore.set(tokens.access_token, tokens.refresh_token);
    const me = await api<Me>("/auth/me");
    setUser(me);
    return me;
  };

  const logout = async () => {
    const refresh = tokenStore.refresh;
    if (refresh) {
      try {
        await api("/auth/logout", { method: "POST", body: { refresh_token: refresh }, auth: false });
      } catch {
        // ignore
      }
    }
    tokenStore.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
