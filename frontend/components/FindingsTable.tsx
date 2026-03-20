"use client";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { ExternalLink, Star, Home, Search, AlertTriangle, TrendingDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Finding, FindingType } from "@/lib/types";
import { api } from "@/lib/api";
import { clsx } from "clsx";

const TYPE_ICONS: Record<FindingType, React.ReactNode> = {
  listing: <Home className="h-3 w-3" />,
  price_change: <TrendingDown className="h-3 w-3" />,
  research_result: <Search className="h-3 w-3" />,
  alert: <AlertTriangle className="h-3 w-3" />,
};

interface Props {
  findings: Finding[];
  onRead?: (id: number) => void;
}

export function FindingsTable({ findings, onRead }: Props) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [readIds, setReadIds] = useState<Set<number>>(new Set());

  async function handleMarkRead(id: number) {
    await api.findings.markRead(id);
    setReadIds((prev) => new Set([...prev, id]));
    onRead?.(id);
  }

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (findings.length === 0) {
    return <div className="text-center text-gray-500 py-12">No findings yet.</div>;
  }

  return (
    <div className="space-y-2">
      {findings.map((finding) => {
        const isNew = finding.is_new && !readIds.has(finding.id);
        const isExpanded = expanded.has(finding.id);
        const meta = finding.metadata_json || {};

        return (
          <div
            key={finding.id}
            className={clsx(
              "rounded-lg border p-4 cursor-pointer transition-colors",
              isNew ? "border-blue-200 bg-blue-50" : "border-gray-100 bg-white",
              "hover:border-gray-300"
            )}
            onClick={() => toggleExpand(finding.id)}
          >
            <div className="flex items-start gap-3">
              <div className={clsx(
                "mt-1 p-1 rounded",
                isNew ? "text-blue-600 bg-blue-100" : "text-gray-400 bg-gray-100"
              )}>
                {TYPE_ICONS[finding.finding_type] ?? TYPE_ICONS.research_result}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-medium text-sm">{finding.title}</span>
                    {isNew && (
                      <Badge className="ml-2 text-[10px] bg-blue-500 text-white py-0">New</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
                    <span className="text-xs text-gray-500">{finding.relevance_score.toFixed(2)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                  <span>{finding.agent_name}</span>
                  <span>·</span>
                  <span>{formatDistanceToNow(new Date(finding.discovered_at), { addSuffix: true })}</span>
                  {(meta as any).price && (
                    <>
                      <span>·</span>
                      <span className="text-green-600 font-medium">{(meta as any).price}</span>
                    </>
                  )}
                  {(meta as any).bedrooms && (
                    <>
                      <span>·</span>
                      <span>{(meta as any).bedrooms} bed</span>
                    </>
                  )}
                </div>

                {isExpanded && (
                  <div className="mt-3 space-y-2" onClick={(e) => e.stopPropagation()}>
                    <p className="text-sm text-gray-700">{finding.summary}</p>

                    {Object.keys(meta).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(meta).map(([k, v]) => (
                          <span key={k} className="text-xs bg-gray-100 rounded px-2 py-0.5">
                            <span className="text-gray-400">{k}:</span> {String(v)}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center gap-2 pt-1">
                      {finding.url && (
                        <a
                          href={finding.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                          View source
                        </a>
                      )}
                      {isNew && (
                        <Button size="sm" variant="outline" className="h-6 text-xs ml-auto"
                          onClick={() => handleMarkRead(finding.id)}>
                          Mark as read
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
