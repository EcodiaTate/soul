// src/pages/Events.tsx
import React, { useEffect, useState } from "react";
import api from "../api/axios";
import NavBar from "../components/NavBar";

interface Event {
  id: string;
  raw_text: string;
  timestamp: string;
  status: string;
  [key: string]: any;
}

const Events: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchEvents = () => {
    setLoading(true);
    api.get("/events")
      .then((res) => setEvents(res.data.reverse()))
      .finally(() => setLoading(false));
  };

  useEffect(fetchEvents, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post("/event", { raw_text: rawText });
    setRawText("");
    fetchEvents();
  };

  return (
    <div className="min-h-screen bg-green-50 p-8">
      <NavBar />
      <h2 className="text-2xl font-bold mb-4 text-emerald-900">Events</h2>
      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          className="flex-1 px-3 py-2 border rounded-lg"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="New event description..."
        />
        <button
          className="bg-emerald-700 text-white px-4 py-2 rounded-lg"
          type="submit"
        >
          Add Event
        </button>
      </form>
      {loading ? (
        <div>Loading events…</div>
      ) : (
        <table className="w-full bg-white rounded-xl shadow">
          <thead>
            <tr>
              <th className="p-3 text-left">Text</th>
              <th className="p-3 text-left">Timestamp</th>
              <th className="p-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td className="p-3">{event.raw_text}</td>
                <td className="p-3">{event.timestamp}</td>
                <td className="p-3">{event.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default Events;
