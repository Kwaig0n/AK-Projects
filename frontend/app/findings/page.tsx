"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FindingsTable } from "@/components/FindingsTable";
import { api } from "@/lib/api";
import type { Finding } from "@/lib/types";

function FindingsContent() {
  const params = useSearchParams();
  const agentId = params.get("agent_id");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  async function load() {
    setLoading(true);
    try {
      const [f, u] = await Promise.all([
        api.findings.list({
          agent_id: agentId ? Number(agentId) : undefined,
          is_new: showUnreadOnly ? true : undefined,
          limit: 100,
        }),
        api.findings.unreadCount(),
      ]);
      setFindings(f);
      setUnreadCount(u.count);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [agentId, showUnreadOnly]);

  async function handleMarkAllRead() {
    await api.findings.markAllRead(agentId ? Number(agentId) : undefined);
    load();
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Findings</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-blue-600 mt-1">{unreadCount} unread</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm"
            onClick={() => setShowUnreadOnly(!showUnreadOnly)}
            className={showUnreadOnly ? "bg-blue-50 border-blue-300" : ""}>
            {showUnreadOnly ? "Show All" : "Unread Only"}
          </Button>
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
              Mark All Read
            </Button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <FindingsTable findings={findings} onRead={() => setUnreadCount((c) => Math.max(0, c - 1))} />
      )}
    </div>
  );
}

export default function FindingsPage() {
  return <Suspense fallback={<div className="p-6 text-gray-400">Loading...</div>}><FindingsContent /></Suspense>;
}
