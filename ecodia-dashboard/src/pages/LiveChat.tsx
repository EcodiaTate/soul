// src/pages/LiveChat.tsx
import React, { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import NavBar from "../components/NavBar";

const WS_URL = "http://localhost:5001";

interface ChatMsg {
  user: string;
  msg: string;
  ts: string;
}

const LiveChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const socket = io(WS_URL);
    socketRef.current = socket;

    socket.on("chat", (msg: ChatMsg) => {
      setMessages((prev) => [...prev, msg]);
    });
    socket.on("server_message", (m: any) => {
      setMessages((prev) => [...prev, { user: "Server", msg: m.msg, ts: new Date().toISOString() }]);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      socketRef.current?.emit("chat", {
        user: "admin",
        msg: input,
      });
      setInput("");
    }
  };

  return (
    <div className="min-h-screen bg-green-50 p-8">
      <NavBar />
      <h2 className="text-2xl font-bold mb-4 text-emerald-900">Live Chat</h2>
      <div className="bg-white rounded-xl shadow p-6 h-96 overflow-y-scroll mb-4">
        {messages.map((m, i) => (
          <div key={i} className="mb-2">
            <span className="font-bold text-emerald-800">{m.user}:</span>{" "}
            <span className="">{m.msg}</span>
            <span className="text-xs text-gray-400 ml-2">{new Date(m.ts).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
      <form onSubmit={send} className="flex gap-2">
        <input
          className="flex-1 px-3 py-2 border rounded-lg"
          placeholder="Type message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="bg-emerald-700 text-white px-4 py-2 rounded-lg" type="submit">
          Send
        </button>
      </form>
    </div>
  );
};

export default LiveChat;
