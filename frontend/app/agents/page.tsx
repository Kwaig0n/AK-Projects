"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Plus, Bot, Home, Search, Play, Pause, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Agent } from "@/lib/types";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try { setAgents(await api.agents.list()); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleToggle(agent: Agent) {
    await api.agents.toggle(agent.id);
    load();
  }

  async function handleRun(agent: Agent) {
    const { run_id } = await api.agents.run(agent.id);
    window.location.href = `/runs/${run_id}`;
  }

  async function handleDelete(agent: Agent) {
    if (!confirm(`Delete agent "${agent.name}"?`)) return;
    await api.agents.delete(agent.id);
    load();
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
        <Link href="/agents/new">
          <Button size="sm"><Plus className="h-4 w-4 mr-1" /> New Agent</Button>
        </Link>
      </div>

      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : agents.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Bot className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No agents yet.</p>
          <Link href="/agents/new">
            <Button className="mt-4" size="sm"><Plus className="h-4 w-4 mr-1" /> Create agent</Button>
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Name</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Type</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Last Run</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Schedule</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">24h Findings</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/agents/${agent.id}`} className="font-medium text-blue-600 hover:underline">
                      {agent.name}
                    </Link>
                    {!agent.is_active && <Badge variant="outline" className="ml-2 text-xs text-gray-400">Inactive</Badge>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-gray-600">
                      {agent.agent_type === "real_estate" ? <Home className="h-3 w-3" /> : <Search className="h-3 w-3" />}
                      {agent.agent_type === "real_estate" ? "Real Estate" : "Research"}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {agent.last_run_at ? formatDistanceToNow(new Date(agent.last_run_at), { addSuffix: true }) : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={agent.last_run_status} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                    {agent.cron_expression || "Manual"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-blue-600">{agent.findings_last_24h}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 justify-end">
                      <Button size="sm" variant="ghost" onClick={() => handleRun(agent)} title="Run now">
                        <Play className="h-3 w-3" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleToggle(agent)}
                        title={agent.is_active ? "Pause" : "Resume"}>
                        {agent.is_active ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3 text-green-600" />}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleDelete(agent)} title="Delete">
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
