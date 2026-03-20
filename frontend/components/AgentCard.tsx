"use client";
import Link from "next/link";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { Play, Square, Settings, Bell, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { AgentAvatar } from "@/components/AgentAvatar";
import { toHuman, fromCron } from "@/lib/schedule";
import type { Agent } from "@/lib/types";
import { api } from "@/lib/api";

interface Props {
  agent: Agent;
  onRunStarted?: (runId: string) => void;
  onStopped?: () => void;
}

// Backend sends UTC datetimes without 'Z' — append it so JS parses them as UTC
function utc(s: string | null | undefined): Date | null {
  if (!s) return null;
  const normalized = s.endsWith("Z") || s.includes("+") ? s : s + "Z";
  return new Date(normalized);
}

export function AgentCard({ agent, onRunStarted, onStopped }: Props) {
  const [stopping, setStopping] = useState(false);
  const isRunning = agent.last_run_status === "running";
  const scheduleLabel = toHuman(fromCron(agent.cron_expression));

  async function handleRun() {
    try {
      const { run_id } = await api.agents.run(agent.id);
      onRunStarted?.(run_id);
      onStopped?.(); // reuse the refresh callback to update card state
    } catch (e) {
      alert(`Failed to start agent: ${e}`);
    }
  }

  async function handleStop() {
    if (!agent.last_run_id) return;
    setStopping(true);
    try {
      await api.runs.stop(agent.last_run_id);
      onStopped?.();
    } catch (e) {
      alert(`Failed to stop run: ${e}`);
    } finally {
      setStopping(false);
    }
  }

  return (
    <Card className={`border-2 overflow-hidden ${isRunning ? "border-blue-200 bg-blue-50/30" : agent.is_active ? "border-green-100" : "border-gray-100"}`}>
      <CardHeader className="pb-3 pt-4 px-4">
        <div className="flex items-start gap-3">
          <AgentAvatar agentType={agent.agent_type} isRunning={isRunning} size={48} />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <Link href={`/agents/${agent.id}`} className="font-semibold text-gray-900 hover:underline leading-tight truncate">
                {agent.name}
              </Link>
              <StatusBadge status={agent.last_run_status} />
            </div>
            {agent.description && (
              <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{agent.description}</p>
            )}
            <p className="text-xs text-gray-400 mt-0.5 capitalize">
              {agent.agent_type === "real_estate" ? "Real Estate Agent" : "Research Agent"}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-400">Last run</span>
            <div className="font-medium">
              {agent.last_run_at
                ? formatDistanceToNow(utc(agent.last_run_at)!, { addSuffix: true })
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
            Next: {formatDistanceToNow(utc(agent.next_run_at)!, { addSuffix: true })}
          </div>
        )}

        {agent.notify_telegram && (
          <div className="flex items-center gap-1 text-xs text-green-600">
            <Bell className="h-3 w-3" />
            <span>Telegram on</span>
          </div>
        )}

        <div className="flex gap-2 pt-1">
          {isRunning ? (
            <Button size="sm" onClick={handleStop} disabled={stopping}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white">
              <Square className="h-3 w-3 mr-1 fill-white" />
              {stopping ? "Stopping..." : "Stop Run"}
            </Button>
          ) : (
            <>
              <Button size="sm" onClick={handleRun} className="flex-1">
                <Play className="h-3 w-3 mr-1" />Run Now
              </Button>
              {(agent.last_run_status === "completed" || agent.last_run_status === "stopped") && agent.last_run_id && (
                <Link href={`/runs/${agent.last_run_id}`}>
                  <Button size="sm" variant="outline" className="text-blue-600 border-blue-200 hover:bg-blue-50">
                    <ExternalLink className="h-3 w-3 mr-1" />Results
                  </Button>
                </Link>
              )}
            </>
          )}
          <Link href={`/agents/${agent.id}`}>
            <Button size="sm" variant="outline"><Settings className="h-3 w-3" /></Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
