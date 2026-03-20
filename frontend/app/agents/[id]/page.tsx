"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, Play, Pause, Trash2, Bell, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { SchedulePicker } from "@/components/SchedulePicker";
import { toCron, fromCron, toHuman } from "@/lib/schedule";
import type { ScheduleConfig } from "@/lib/schedule";
import { api } from "@/lib/api";
import type { Agent, Run, Finding } from "@/lib/types";

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [running, setRunning] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(false);
  const [schedule, setSchedule] = useState<ScheduleConfig | null>(null);
  const [savingSchedule, setSavingSchedule] = useState(false);

  async function load() {
    const [a, r, f] = await Promise.all([
      api.agents.get(Number(id)),
      api.runs.list(Number(id), 10),
      api.findings.list({ agent_id: Number(id), limit: 5 }),
    ]);
    setAgent(a);
    setRuns(r);
    setFindings(f);
    setSchedule(fromCron(a.cron_expression));
  }

  useEffect(() => { load(); }, [id]);

  async function handleRun() {
    setRunning(true);
    try {
      const { run_id } = await api.agents.run(Number(id));
      router.push(`/runs/${run_id}`);
    } finally { setRunning(false); }
  }

  async function handleToggle() {
    await api.agents.toggle(Number(id));
    load();
  }

  async function handleDelete() {
    if (!confirm(`Delete agent "${agent?.name}"?`)) return;
    await api.agents.delete(Number(id));
    router.push("/agents");
  }

  async function handleSaveSchedule() {
    if (!schedule) return;
    setSavingSchedule(true);
    try {
      await api.agents.update(Number(id), { cron_expression: toCron(schedule) });
      setEditingSchedule(false);
      load();
    } finally { setSavingSchedule(false); }
  }

  if (!agent || !schedule) return <div className="p-6 text-gray-400">Loading...</div>;

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <Link href="/agents" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Agents
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
          {agent.description && <p className="text-gray-500 text-sm mt-1">{agent.description}</p>}
        </div>
        <div className="flex gap-2 shrink-0">
          <Button size="sm" onClick={handleRun} disabled={running}>
            <Play className="h-4 w-4 mr-1" />{running ? "Starting..." : "Run Now"}
          </Button>
          <Button size="sm" variant="outline" onClick={handleToggle}>
            {agent.is_active ? <><Pause className="h-4 w-4 mr-1" />Pause</> : <><Play className="h-4 w-4 mr-1" />Resume</>}
          </Button>
          <Button size="sm" variant="outline" onClick={handleDelete}
            className="text-red-500 border-red-200 hover:bg-red-50">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Status", value: agent.is_active ? "Active" : "Inactive", color: agent.is_active ? "text-green-600" : "text-gray-400" },
          { label: "Type", value: agent.agent_type === "real_estate" ? "Real Estate" : "Research", color: "text-blue-600" },
          { label: "Findings (24h)", value: String(agent.findings_last_24h), color: "text-purple-600" },
        ].map(({ label, value, color }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <div className="text-xs text-gray-400 mb-1">{label}</div>
              <div className={`font-medium text-sm ${color}`}>{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Schedule card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Schedule
            </CardTitle>
            <Button size="sm" variant="ghost" onClick={() => setEditingSchedule(!editingSchedule)}>
              {editingSchedule ? "Cancel" : "Edit"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {editingSchedule ? (
            <div className="space-y-3">
              <SchedulePicker value={schedule} onChange={setSchedule} />
              <Button size="sm" onClick={handleSaveSchedule} disabled={savingSchedule}>
                {savingSchedule ? "Saving..." : "Save Schedule"}
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium text-gray-700">{toHuman(schedule)}</span>
              {agent.cron_expression && (
                <span className="font-mono text-xs text-gray-400">({agent.cron_expression})</span>
              )}
              {agent.next_run_at && (
                <span className="text-gray-400 text-xs">
                  · next {formatDistanceToNow(new Date(agent.next_run_at), { addSuffix: true })}
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {agent.notify_telegram && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <Bell className="h-4 w-4" /> Telegram notifications enabled
        </div>
      )}

      <Card>
        <CardHeader><CardTitle className="text-sm">Search Criteria</CardTitle></CardHeader>
        <CardContent>
          <pre className="text-xs bg-gray-950 text-gray-200 rounded-lg p-4 overflow-auto max-h-64">
            {JSON.stringify(agent.criteria, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Recent Runs</CardTitle>
            <Link href={`/runs?agent_id=${agent.id}`} className="text-xs text-blue-600 hover:underline">View all</Link>
          </div>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <div className="text-gray-400 text-sm">No runs yet.</div>
          ) : (
            <div className="space-y-1">
              {runs.map((run) => (
                <Link key={run.run_id} href={`/runs/${run.run_id}`}>
                  <div className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <div className="flex items-center gap-3">
                      <StatusBadge status={run.status} />
                      <span className="text-xs text-gray-500">
                        {run.started_at ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true }) : "—"}
                      </span>
                      <span className="text-xs text-gray-400">via {run.triggered_by}</span>
                    </div>
                    <div className="text-xs text-blue-600">{run.findings_count} findings</div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {findings.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Recent Findings</CardTitle>
              <Link href={`/findings?agent_id=${agent.id}`} className="text-xs text-blue-600 hover:underline">View all</Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {findings.map((f) => (
              <div key={f.id} className="flex items-start justify-between gap-2 p-2 rounded hover:bg-gray-50">
                <div>
                  <p className="text-sm font-medium">{f.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{f.summary}</p>
                </div>
                <Badge variant="outline" className="text-xs shrink-0">{f.relevance_score.toFixed(2)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
