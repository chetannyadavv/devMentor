import { createContext, useContext, useState, useCallback } from "react";
import { api, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    try {
      const me = await api.get("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setInitializing(false);
    }
  }, []);

  // On first mount, if a token is already stored (from a previous
  // session), try to resolve who it belongs to -- keeps the user logged
  // in across page refreshes instead of forcing a fresh login every time.
  useState(() => {
    loadCurrentUser();
  });

  async function login(username, password) {
    const body = new URLSearchParams();
    body.set("username", username);
    body.set("password", password);
    const result = await api.post("/auth/login", body);
    setToken(result.access_token);
    await loadCurrentUser();
  }

  async function register(username, email, password) {
    await api.post("/auth/register", { username, email, password });
    await login(username, password);
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, initializing, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
