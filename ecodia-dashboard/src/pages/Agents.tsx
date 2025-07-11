import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Drawer, DrawerContent, DrawerTrigger } from "@/components/ui/drawer";
import { io, Socket } from "socket.io-client";

const API_URL = "/api";

type Agent = {
  agent_id: string;
  name: string;
  model: string;
  mood: string;
  energy: number;
  persona: any;
  archived: boolean;
  memory: any[];
  log: any[];
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSpawn, setShowSpawn] = useState(false);
  const [spawnFields, setSpawnFields] = useState({ name: "", model: "gpt-4", mood: "neutral", persona: "" });
  const [inspectAgent, setInspectAgent] = useState<Agent | null>(null);
  const [inspectTab, setInspectTab] = useState<"memory" | "log">("memory");
  const [moodInput, setMoodInput] = useState("");
  const socketRef = useRef<Socket | null>(null);

  async function fetchAgents() {
    setLoading(true);
    const res = await fetch(`${API_URL}/agents`);
    const data = await res.json();
    // Remove duplicate agent_ids
    const unique = new Map();
    for (const a of data) unique.set(a.agent_id, a);
    setAgents(Array.from(unique.values()));
    setLoading(false);
  }

  useEffect(() => {
    fetchAgents();

    // Setup Socket.IO (live agent updates)
    if (!socketRef.current) {
      socketRef.current = io(API_URL.replace(/^\/api$/, ""), {
        transports: ["websocket"],
        path: "/socket.io"
      });

      socketRef.current.on("agent:spawn", (agent: Agent) => {
        setAgents(prev => {
          const filtered = prev.filter(a => a.agent_id !== agent.agent_id);
          return [...filtered, agent];
        });
      });

      socketRef.current.on("agent:retire", ({ agent_id }) => {
        setAgents(prev =>
          prev.map(a => a.agent_id === agent_id ? { ...a, archived: true } : a)
        );
      });
    }
    return () => {
      socketRef.current?.disconnect();
    };
    // eslint-disable-next-line
  }, []);

  async function handleSpawn() {
    const payload = {
      name: spawnFields.name,
      model: spawnFields.model,
      mood: spawnFields.mood,
      persona: spawnFields.persona ? { summary: spawnFields.persona } : undefined,
    };
    await fetch(`${API_URL}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setShowSpawn(false);
    setSpawnFields({ name: "", model: "gpt-4", mood: "neutral", persona: "" });
    // No need to fetchAgents—real-time update handles it!
  }

  async function retireAgent(agent_id: string) {
    await fetch(`${API_URL}/agent/${agent_id}/retire`, { method: "POST" });
    // Real-time update will handle UI
  }

  async function setAgentMood(agent_id: string) {
    await fetch(`${API_URL}/agent/${agent_id}/mood`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mood: moodInput }),
    });
    setMoodInput("");
    fetchAgents();
  }

  async function triggerDream(agent_id: string) {
    await fetch(`${API_URL}/agent/${agent_id}/dream`, { method: "POST" });
    fetchAgents();
    alert("Dream triggered!");
  }

  function handleInspect(agent: Agent) {
    setInspectTab("memory");
    setInspectAgent(agent);
  }

  function moodColor(mood: string) {
    if (mood === "curious") return "text-blue-500";
    if (mood === "critical") return "text-red-500";
    if (mood === "reflective") return "text-purple-500";
    if (mood === "tired") return "text-gray-400";
    if (mood === "optimistic") return "text-green-600";
    if (mood === "chaotic") return "text-pink-600";
    return "";
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Ecodia Soul Dashboard</h1>
          <div className="text-sm text-gray-500 mt-1">
            Agents alive: {agents.filter(a => !a.archived).length} / {agents.length}
          </div>
        </div>
        <Dialog open={showSpawn} onOpenChange={setShowSpawn}>
          <DialogTrigger asChild>
            <Button>Spawn New Agent</Button>
          </DialogTrigger>
          <DialogContent>
            <h2 className="text-xl font-semibold mb-2">Spawn New Agent</h2>
            <div className="space-y-2">
              <Input placeholder="Name" value={spawnFields.name} onChange={e => setSpawnFields(f => ({ ...f, name: e.target.value }))} />
              <select className="w-full p-2 rounded" value={spawnFields.model} onChange={e => setSpawnFields(f => ({ ...f, model: e.target.value }))}>
                <option value="gpt-4">GPT-4</option>
                <option value="gemini-1.5-pro">Gemini 1.5</option>
                <option value="claude-3-opus">Claude 3</option>
              </select>
              <Input placeholder="Mood" value={spawnFields.mood} onChange={e => setSpawnFields(f => ({ ...f, mood: e.target.value }))} />
              <Input placeholder="Persona (optional)" value={spawnFields.persona} onChange={e => setSpawnFields(f => ({ ...f, persona: e.target.value }))} />
              <Button className="w-full mt-2" onClick={handleSpawn}>Create Agent</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      <Card>
        <CardContent className="p-4">
          <table className="min-w-full">
            <thead>
              <tr>
                <th className="text-left p-2">Name</th>
                <th className="text-left p-2">Model</th>
                <th className="text-left p-2">Mood</th>
                <th className="text-left p-2">Energy</th>
                <th className="text-left p-2">Archived</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? <tr><td colSpan={6}>Loading…</td></tr> : agents.map(agent => (
                <tr key={agent.agent_id} className={agent.archived ? "opacity-60" : ""}>
                  <td className="p-2 flex items-center gap-2">
                    <span className="inline-block w-7 h-7 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-bold text-lg">
                      {agent.name[0]}
                    </span>
                    {agent.name}
                  </td>
                  <td className="p-2">{agent.model}</td>
                  <td className={`p-2 font-semibold ${moodColor(agent.mood)}`}>{agent.mood}</td>
                  <td className="p-2">{agent.energy?.toFixed(2)}</td>
                  <td className="p-2">{agent.archived ? "Yes" : "No"}</td>
                  <td className="p-2">
                    <Drawer>
                      <DrawerTrigger asChild>
                        <Button size="sm" variant="outline" onClick={() => handleInspect(agent)}>Inspect</Button>
                      </DrawerTrigger>
                      <DrawerContent>
                        {inspectAgent && inspectAgent.agent_id === agent.agent_id && (
                          <div className="p-4">
                            <h3 className="font-semibold">{agent.name} — Details</h3>
                            <div className="text-xs text-gray-400 mb-2">ID: {agent.agent_id}</div>
                            <div><b>Mood:</b> {agent.mood}</div>
                            <div><b>Energy:</b> {agent.energy?.toFixed(2)}</div>
                            <div><b>Persona:</b> {JSON.stringify(agent.persona)}</div>
                            <div><b>Memory count:</b> {agent.memory?.length}</div>
                            <div className="flex gap-2 mt-4 mb-2">
                              <Button
                                variant={inspectTab === "memory" ? "default" : "outline"}
                                size="sm"
                                onClick={() => setInspectTab("memory")}
                              >
                                Memory
                              </Button>
                              <Button
                                variant={inspectTab === "log" ? "default" : "outline"}
                                size="sm"
                                onClick={() => setInspectTab("log")}
                              >
                                Log
                              </Button>
                            </div>
                            {inspectTab === "memory" ? (
                              <div className="max-h-48 overflow-auto text-xs bg-gray-100 rounded p-2">
                                {agent.memory && agent.memory.length > 0 ? agent.memory.slice(-25).reverse().map((m, i) => (
                                  <div key={i} className="mb-2">
                                    <div>
                                      <b>{m.timestamp}:</b> {m.event?.raw_text || JSON.stringify(m.event)}
                                    </div>
                                    <div className="ml-2 text-gray-500">
                                      Mood: {m.mood}, Impact: {m.impact}
                                    </div>
                                  </div>
                                )) : <span>No memory yet.</span>}
                              </div>
                            ) : (
                              <div className="max-h-48 overflow-auto text-xs bg-gray-100 rounded p-2">
                                {agent.log && agent.log.length > 0 ? agent.log.slice(-25).reverse().map((l, i) => (
                                  <div key={i}>{l.timestamp}: {l.message}</div>
                                )) : <span>No log yet.</span>}
                              </div>
                            )}
                            <div className="mt-4">
                              <h4 className="font-semibold mb-1">Set Mood</h4>
                              <div className="flex gap-2">
                                <Input
                                  placeholder="Type new mood"
                                  value={moodInput}
                                  onChange={e => setMoodInput(e.target.value)}
                                />
                                <Button
                                  variant="secondary"
                                  onClick={() => setAgentMood(agent.agent_id)}
                                  disabled={!moodInput}
                                >
                                  Save
                                </Button>
                              </div>
                              <Button
                                className="mt-3"
                                variant="ghost"
                                onClick={() => triggerDream(agent.agent_id)}
                              >
                                🌙 Trigger Dream
                              </Button>
                            </div>
                          </div>
                        )}
                      </DrawerContent>
                    </Drawer>
                    {!agent.archived && (
                      <Button
                        size="sm"
                        variant="destructive"
                        className="ml-2"
                        onClick={() => retireAgent(agent.agent_id)}
                      >
                        Retire
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
