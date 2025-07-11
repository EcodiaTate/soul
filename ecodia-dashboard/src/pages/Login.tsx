// src/pages/Login.tsx
import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";

const Login: React.FC = () => {
  const { login, loading, error } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await login(username, password);
    if (ok) {
      setSuccess(true);
      window.location.href = "/Dashboard";
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-100 to-green-300">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-2xl shadow-xl flex flex-col w-96"
      >
        <h1 className="text-3xl font-bold mb-4 text-emerald-800">Ecodia Admin</h1>
        <label className="mb-2 text-emerald-900 font-semibold">Username</label>
        <input
          className="mb-4 px-3 py-2 border rounded-lg"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />
        <label className="mb-2 text-emerald-900 font-semibold">Password</label>
        <input
          className="mb-4 px-3 py-2 border rounded-lg"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <div className="text-red-600 mb-2">{error}</div>}
        <button
          type="submit"
          className="bg-emerald-700 text-white rounded-lg py-2 font-bold hover:bg-emerald-800"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
        {success && (
          <div className="text-green-700 mt-2 font-semibold">
            Login successful! Redirecting...
          </div>
        )}
      </form>
    </div>
  );
};

export default Login;
