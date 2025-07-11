// src/hooks/useAuth.ts
import { useState } from "react";
import api from "../api/axios";

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/login", { username, password });
      localStorage.setItem("token", res.data.access_token);
      setLoading(false);
      return true;
    } catch (e: any) {
      setError(e.response?.data?.error || "Login failed");
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  const isAuthenticated = !!localStorage.getItem("token");

  return { login, logout, isAuthenticated, loading, error };
}
