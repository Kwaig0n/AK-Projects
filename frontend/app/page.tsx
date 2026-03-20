"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Bot, Play, Search, TrendingUp, Plus, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentCard } from "@/components/AgentCard";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Agent, Run } from "@/lib/types";

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [a, r, u] = await Promise.all([
        api.agents.list(),
        api.runs.list(undefined, 10),
        api.findings.unreadCount(),
      ]);
      setAgents(a);
      setRuns(r);
      setUnread(u.count);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const activeAgents = agents.filter((a) => a.is_active).length;
  const runsToday = runs.filter((r) => {
    if (!r.started_at) return false;
    const d = new Date(r.started_at);
    const now = new Date();
    return d.toDateString() === now.toDateString();
  }).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Your AI agent ecosystem at a glance</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
          <Link href="/agents/new">
            <Button size="sm">
              <Plus className="h-4 w-4 mr-1" /> New Agent
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Agents", value: agents.length, icon: Bot, color: "text-blue-600" },
          { label: "Active", value: activeAgents, icon: Play, color: "text-green-600" },
          { label: "Runs Today", value: runsToday, icon: TrendingUp, color: "text-purple-600" },
          { label: "New Findings", value: unread, icon: Search, color: "text-orange-500" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gray-100 ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{value}</div>
                <div className="text-xs text-gray-400">{label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Agent grid */}
        <div className="col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-700">Agents</h2>
            <Link href="/agents" className="text-sm text-blue-600 hover:underline">View all</Link>
          </div>
          {loading ? (
            <div className="text-gray-400 text-sm">Loading agents...</div>
          ) : agents.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center">
                <Bot className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 mb-3">No agents yet</p>
                <Link href="/agents/new">
                  <Button size="sm"><Plus className="h-4 w-4 mr-1" /> Create your first agent</Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          )}
        </div>

        {/* Recent runs */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-700">Recent Runs</h2>
            <Link href="/runs" className="text-sm text-blue-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-2">
            {runs.length === 0 ? (
              <div className="text-gray-400 text-sm">No runs yet.</div>
            ) : (
              runs.map((run) => (
                <Link key={run.run_id} href={`/runs/${run.run_id}`}>
                  <Card className="hover:border-blue-200 transition-colors cursor-pointer">
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium truncate">{run.agent_name}</span>
                        <StatusBadge status={run.status} />
                      </div>
                      <div className="text-xs text-gray-400 mt-1 flex gap-2">
                        <span>{run.findings_count} findings</span>
                        {run.started_at && (
                          <span>· {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
