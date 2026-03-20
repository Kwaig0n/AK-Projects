"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Run } from "@/lib/types";

function RunsContent() {
  const params = useSearchParams();
  const agentId = params.get("agent_id");
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.runs.list(agentId ? Number(agentId) : undefined, 100)
      .then(setRuns)
      .finally(() => setLoading(false));
  }, [agentId]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Runs</h1>
      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : runs.length === 0 ? (
        <div className="text-gray-400 py-12 text-center">No runs yet.</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Agent</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Triggered By</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Started</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Duration</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Findings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {runs.map((run) => (
                <tr key={run.run_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/runs/${run.run_id}`} className="text-blue-600 hover:underline font-medium">
                      {run.agent_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={run.status} /></td>
                  <td className="px-4 py-3 text-gray-500 capitalize">{run.triggered_by}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {run.started_at ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true }) : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {run.duration_seconds ? `${run.duration_seconds.toFixed(0)}s` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-blue-600">{run.findings_count}</span>
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

export default function RunsPage() {
  return <Suspense fallback={<div className="p-6 text-gray-400">Loading...</div>}><RunsContent /></Suspense>;
}
