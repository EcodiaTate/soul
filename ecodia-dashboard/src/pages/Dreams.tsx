// src/pages/Dreams.tsx
import React, { useEffect, useState } from "react";
import api from "../api/axios";
import NavBar from "../components/NavBar";

interface Dream {
  [key: string]: any;
}

const Dreams: React.FC = () => {
  const [dreams, setDreams] = useState<Dream[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dreams")
      .then((res) => setDreams(res.data.reverse()))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-green-50 p-8">
      <NavBar />
      <h2 className="text-2xl font-bold mb-4 text-emerald-900">Dreams</h2>
      {loading ? (
        <div>Loading dreams…</div>
      ) : (
        <ul className="space-y-4">
          {dreams.map((dream, i) => (
            <li key={i} className="bg-white rounded-xl shadow p-4 font-mono text-sm">
              <pre>{JSON.stringify(dream, null, 2)}</pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Dreams;
