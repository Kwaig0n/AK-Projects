"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

function utc(s: string | null | undefined): Date | null {
  if (!s) return null;
  const normalized = s.endsWith("Z") || s.includes("+") ? s : s + "Z";
  return new Date(normalized);
}
import { ArrowLeft, Square } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { RunLogViewer } from "@/components/RunLogViewer";
import { FindingsTable } from "@/components/FindingsTable";
import { api } from "@/lib/api";
import type { Run, Finding } from "@/lib/types";

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [stopping, setStopping] = useState(false);

  async function handleStop() {
    setStopping(true);
    try { await api.runs.stop(runId); }
    catch (e) { console.error(e); }
    finally { setStopping(false); }
  }

  useEffect(() => {
    api.runs.get(runId).then(setRun);
    // Poll until complete
    const interval = setInterval(async () => {
      const r = await api.runs.get(runId);
      setRun(r);
      if (r.status === "completed" || r.status === "failed" || r.status === "stopped") {
        clearInterval(interval);
        const f = await api.findings.list({ agent_id: r.agent_id, limit: 50 });
        setFindings(f.filter((fi) => fi.run_id === r.id));
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [runId]);

  if (!run) return <div className="p-6 text-gray-400">Loading...</div>;

  const isComplete = run.status === "completed" || run.status === "failed" || run.status === "stopped";

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <Link href="/runs" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Runs
      </Link>

      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-gray-900">{run.agent_name}</h1>
        <StatusBadge status={run.status} />
        {run.status === "running" && (
          <Button size="sm" variant="outline" onClick={handleStop} disabled={stopping}
            className="text-red-600 border-red-200 hover:bg-red-50">
            <Square className="h-3 w-3 mr-1 fill-red-500" />
            {stopping ? "Stopping..." : "Stop Run"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-3 text-sm">
        {[
          { label: "Triggered by", value: run.triggered_by },
          { label: "Started", value: run.started_at ? formatDistanceToNow(utc(run.started_at)!, { addSuffix: true }) : "—" },
          { label: "Duration", value: run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : run.status === "running" ? "Running..." : "—" },
          { label: "Findings", value: String(run.findings_count) },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="p-3">
              <div className="text-xs text-gray-400">{label}</div>
              <div className="font-medium mt-0.5">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {run.tokens_used > 0 && (
        <p className="text-xs text-gray-400">Tokens used: {run.tokens_used.toLocaleString()}</p>
      )}

      {run.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          <strong>Error:</strong> {run.error_message}
        </div>
      )}

      <RunLogViewer runId={runId} initialLogs={run.log_entries} isComplete={isComplete} />

      {isComplete && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Findings ({findings.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <FindingsTable findings={findings} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
