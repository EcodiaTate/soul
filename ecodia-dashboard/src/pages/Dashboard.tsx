// src/pages/Dashboard.tsx
import React, { useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../hooks/useAuth";

interface Agent {
  agent_id: string;
  name: string;
  model: string;
  mood: string;
  energy: number;
  archived: boolean;
}

const Dashboard: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();

  useEffect(() => {
    api.get("/agents")
      .then((res) => setAgents(res.data))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-green-50 p-8">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-3xl font-bold text-emerald-900">Ecodia Soul Dashboard</h2>
        <button
          className="bg-red-500 text-white px-4 py-2 rounded-lg font-semibold"
          onClick={logout}
        >
          Logout
        </button>
      </div>
      {loading ? (
        <div>Loading agents…</div>
      ) : (
        <table className="w-full bg-white rounded-xl shadow-xl">
          <thead>
            <tr>
              <th className="p-3 text-left">Name</th>
              <th className="p-3 text-left">Model</th>
              <th className="p-3 text-left">Mood</th>
              <th className="p-3 text-left">Energy</th>
              <th className="p-3 text-left">Archived</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.agent_id}>
                <td className="p-3">{agent.name}</td>
                <td className="p-3">{agent.model}</td>
                <td className="p-3">{agent.mood}</td>
                <td className="p-3">{agent.energy.toFixed(2)}</td>
                <td className="p-3">{agent.archived ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default Dashboard;
