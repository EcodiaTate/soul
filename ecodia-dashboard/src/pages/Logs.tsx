// src/pages/Logs.tsx
import React, { useEffect, useState } from "react";
import api from "../api/axios";
import NavBar from "../components/NavBar";

const LOGTYPES = ["api", "world", "peer_review", "dream"];

const Logs: React.FC = () => {
  const [logType, setLogType] = useState(LOGTYPES[0]);
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.get(`/logs/${logType}`)
      .then((res) => setLines(res.data))
      .finally(() => setLoading(false));
  }, [logType]);

  return (
    <div className="min-h-screen bg-green-50 p-8">
      <NavBar />
      <h2 className="text-2xl font-bold mb-4 text-emerald-900">Logs</h2>
      <div className="mb-4">
        {LOGTYPES.map((type) => (
          <button
            key={type}
            className={
              "px-3 py-1 rounded mr-2 font-medium " +
              (type === logType
                ? "bg-emerald-700 text-white"
                : "bg-green-100 text-emerald-900 hover:bg-green-200")
            }
            onClick={() => setLogType(type)}
          >
            {type}
          </button>
        ))}
      </div>
      <div className="bg-black text-green-200 rounded-lg p-4 font-mono text-xs overflow-x-auto max-h-[500px]">
        {loading ? (
          <div>Loading logs…</div>
        ) : (
          lines.map((line, i) => <div key={i}>{line}</div>)
        )}
      </div>
    </div>
  );
};

export default Logs;
