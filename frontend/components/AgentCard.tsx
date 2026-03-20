"use client";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Play, Settings, Home, Search, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { toHuman, fromCron } from "@/lib/schedule";
import type { Agent } from "@/lib/types";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

interface Props {
  agent: Agent;
  onRunStarted?: (runId: string) => void;
}

export function AgentCard({ agent, onRunStarted }: Props) {
  const router = useRouter();
  const icon = agent.agent_type === "real_estate" ? <Home className="h-4 w-4" /> : <Search className="h-4 w-4" />;
  const scheduleLabel = toHuman(fromCron(agent.cron_expression));

  async function handleRun() {
    try {
      const { run_id } = await api.agents.run(agent.id);
      onRunStarted?.(run_id);
      router.push(`/runs/${run_id}`);
    } catch (e) {
      alert(`Failed to start agent: ${e}`);
    }
  }

  return (
    <Card className={`border-2 ${agent.is_active ? "border-green-100" : "border-gray-100"}`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-blue-600">{icon}</span>
            <CardTitle className="text-base">
              <Link href={`/agents/${agent.id}`} className="hover:underline">{agent.name}</Link>
            </CardTitle>
          </div>
          <StatusBadge status={agent.last_run_status} />
        </div>
        {agent.description && <p className="text-sm text-gray-500 mt-1">{agent.description}</p>}
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-400">Last run</span>
            <div className="font-medium">
              {agent.last_run_at
                ? formatDistanceToNow(new Date(agent.last_run_at), { addSuffix: true })
                : "Never"}
            </div>
          </div>
          <div>
            <span className="text-gray-400">Findings (24h)</span>
            <div className="font-medium text-blue-600">{agent.findings_last_24h}</div>
          </div>
        </div>

        <div className="text-xs text-gray-500 flex items-center gap-1">
          <span className="text-gray-400">Schedule:</span>
          <span className={agent.cron_expression ? "text-gray-700 font-medium" : "text-gray-400"}>
            {scheduleLabel}
          </span>
        </div>

        {agent.next_run_at && (
          <div className="text-xs text-gray-400">
            Next: {formatDistanceToNow(new Date(agent.next_run_at), { addSuffix: true })}
          </div>
        )}

        {agent.notify_telegram && (
          <div className="flex items-center gap-1 text-xs text-green-600">
            <Bell className="h-3 w-3" />
            <span>Telegram on</span>
          </div>
        )}

        <div className="flex gap-2 pt-1">
          <Button size="sm" onClick={handleRun} className="flex-1">
            <Play className="h-3 w-3 mr-1" />Run Now
          </Button>
          <Link href={`/agents/${agent.id}`}>
            <Button size="sm" variant="outline"><Settings className="h-3 w-3" /></Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
