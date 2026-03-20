"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Bot, Play, Search, TrendingUp, Plus, RefreshCw, X, CheckCircle } from "lucide-react";

// Backend sends UTC datetimes without 'Z'
function utc(s: string | null | undefined): Date | null {
  if (!s) return null;
  const normalized = s.endsWith("Z") || s.includes("+") ? s : s + "Z";
  return new Date(normalized);
}
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentCard } from "@/components/AgentCard";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Agent, Run } from "@/lib/types";

interface CompletionToast {
  id: string;
  agentName: string;
  runId: string;
  findingsCount: number;
  status: "completed" | "stopped" | "failed";
}

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<CompletionToast[]>([]);
  const prevAgentsRef = useRef<Record<number, string>>({});

  function dismissToast(id: string) {
    setToasts((t) => t.filter((x) => x.id !== id));
  }

  async function load() {
    setLoading(true);
    try {
      const [a, r, u] = await Promise.all([
        api.agents.list(),
        api.runs.list(undefined, 10),
        api.findings.unreadCount(),
      ]);

      // Detect runs that just finished since last poll
      const prev = prevAgentsRef.current;
      const newToasts: CompletionToast[] = [];
      for (const agent of a) {
        const wasRunning = prev[agent.id] === "running";
        const isDone =
          agent.last_run_status === "completed" ||
          agent.last_run_status === "stopped" ||
          agent.last_run_status === "failed";
        if (wasRunning && isDone && agent.last_run_id) {
          newToasts.push({
            id: agent.last_run_id,
            agentName: agent.name,
            runId: agent.last_run_id,
            findingsCount: agent.findings_last_24h,
            status: agent.last_run_status as "completed" | "stopped" | "failed",
          });
        }
        prev[agent.id] = agent.last_run_status ?? "";
      }
      if (newToasts.length) {
        setToasts((t) => [...t, ...newToasts]);
        // Auto-dismiss after 12s
        newToasts.forEach((toast) => {
          setTimeout(() => dismissToast(toast.id), 12000);
        });
      }

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

  // Auto-refresh every 5s while any agent is running
  useEffect(() => {
    const anyRunning = agents.some((a) => a.last_run_status === "running");
    if (!anyRunning) return;
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [agents]);

  const activeAgents = agents.filter((a) => a.is_active).length;
  const runsToday = runs.filter((r) => {
    if (!r.started_at) return false;
    const d = utc(r.started_at);
    if (!d) return false;
    const now = new Date();
    return d.toDateString() === now.toDateString();
  }).length;

  return (
    <div className="p-6 space-y-6">
      {/* Completion toasts */}
      {toasts.length > 0 && (
        <div className="space-y-2">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`flex items-center justify-between gap-3 rounded-lg border px-4 py-3 text-sm shadow-sm
                ${toast.status === "completed"
                  ? "bg-green-50 border-green-200 text-green-800"
                  : toast.status === "stopped"
                  ? "bg-orange-50 border-orange-200 text-orange-800"
                  : "bg-red-50 border-red-200 text-red-800"}`}
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
                <span>
                  <strong>{toast.agentName}</strong> run {toast.status} —{" "}
                  <strong>{toast.findingsCount} finding{toast.findingsCount !== 1 ? "s" : ""}</strong> in the last 24h
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Link href={`/runs/${toast.runId}`}>
                  <Button size="sm" variant="outline"
                    className={`text-xs h-7 ${toast.status === "completed" ? "border-green-300 hover:bg-green-100" : "border-orange-300 hover:bg-orange-100"}`}>
                    View Results
                  </Button>
                </Link>
                <button onClick={() => dismissToast(toast.id)} className="opacity-60 hover:opacity-100">
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

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
                <AgentCard key={agent.id} agent={agent} onStopped={load} />
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
                          <span>· {formatDistanceToNow(utc(run.started_at)!, { addSuffix: true })}</span>
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
