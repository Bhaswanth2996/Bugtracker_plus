import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, parseApiError, setAuthToken } from "../services/api";

const AuthContext = createContext(null);

const STORAGE_KEY = "bugtracker_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function bootstrap() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        setAuthToken(token);
        const response = await api.me();
        setUser(response.data);
      } catch (err) {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setAuthToken(null);
        setError(parseApiError(err));
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      error,
      async login(email, password) {
        const response = await api.login({ email, password });
        const nextToken = response.data.access_token;
        localStorage.setItem(STORAGE_KEY, nextToken);
        setAuthToken(nextToken);
        setToken(nextToken);
        setUser(response.data.user);
        setError(null);
      },
      async register(name, email, password) {
        const response = await api.register({ name, email, password });
        const nextToken = response.data.access_token;
        localStorage.setItem(STORAGE_KEY, nextToken);
        setAuthToken(nextToken);
        setToken(nextToken);
        setUser(response.data.user);
        setError(null);
      },
      async refreshMe() {
        const response = await api.me();
        setUser(response.data);
      },
      logout() {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
        setAuthToken(null);
      },
      setError,
    }),
    [token, user, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
