"use client";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { ExternalLink, Star, Home, Search, AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";
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

const YIELD_RATING_CONFIG: Record<string, { label: string; className: string }> = {
  strong:        { label: "Strong Yield",        className: "bg-green-100 text-green-700 border-green-200" },
  above_average: { label: "Above Avg Yield",     className: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  average:       { label: "Avg Yield",           className: "bg-blue-100 text-blue-700 border-blue-200" },
  below_average: { label: "Below Avg Yield",     className: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  weak:          { label: "Weak Yield",          className: "bg-red-100 text-red-600 border-red-200" },
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
        const meta = (finding.metadata_json || {}) as Record<string, any>;
        const yieldCfg = meta.yield_rating ? YIELD_RATING_CONFIG[meta.yield_rating] : null;

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
                "mt-1 p-1 rounded shrink-0",
                isNew ? "text-blue-600 bg-blue-100" : "text-gray-400 bg-gray-100"
              )}>
                {TYPE_ICONS[finding.finding_type] ?? TYPE_ICONS.research_result}
              </div>

              <div className="flex-1 min-w-0">
                {/* Title row */}
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm">{finding.title}</span>
                    {isNew && (
                      <Badge className="text-[10px] bg-blue-500 text-white py-0">New</Badge>
                    )}
                    {yieldCfg && (
                      <Badge variant="outline" className={clsx("text-[10px] py-0", yieldCfg.className)}>
                        {yieldCfg.label}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
                    <span className="text-xs text-gray-500">{finding.relevance_score.toFixed(2)}</span>
                  </div>
                </div>

                {/* Key stats row */}
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400 flex-wrap">
                  <span>{finding.agent_name}</span>
                  <span>·</span>
                  <span>{formatDistanceToNow(new Date(finding.discovered_at), { addSuffix: true })}</span>
                  {meta.price && (
                    <><span>·</span><span className="text-green-600 font-medium">{meta.price}</span></>
                  )}
                  {meta.bedrooms && (
                    <><span>·</span><span>{meta.bedrooms} bed</span></>
                  )}
                  {meta.bathrooms && (
                    <span>{meta.bathrooms} bath</span>
                  )}
                  {meta.rental_yield_pct && (
                    <><span>·</span>
                    <span className={clsx(
                      "font-semibold",
                      meta.yield_index >= 1.05 ? "text-green-600" :
                      meta.yield_index <= 0.95 ? "text-orange-500" : "text-gray-600"
                    )}>
                      {meta.rental_yield_pct}% yield
                    </span></>
                  )}
                  {meta.yield_index && (
                    <span className="text-gray-400">
                      (index: {meta.yield_index}x)
                    </span>
                  )}
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="mt-3 space-y-3" onClick={(e) => e.stopPropagation()}>
                    <p className="text-sm text-gray-700">{finding.summary}</p>

                    {/* Yield breakdown card */}
                    {meta.rental_yield_pct && (
                      <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 space-y-2">
                        <div className="flex items-center gap-1 text-xs font-semibold text-gray-600">
                          <TrendingUp className="h-3 w-3" />
                          Rental Yield Analysis
                        </div>
                        <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                          <YieldRow label="Est. weekly rent"
                            value={meta.estimated_weekly_rent ? `$${meta.estimated_weekly_rent}/wk` : "—"} />
                          <YieldRow label="Annual income"
                            value={meta.annual_rental_income ? `$${meta.annual_rental_income?.toLocaleString()}` : "—"} />
                          <YieldRow label="Rental yield"
                            value={meta.rental_yield_pct ? `${meta.rental_yield_pct}%` : "—"}
                            highlight />
                          <YieldRow label="Suburb avg yield"
                            value={meta.suburb_avg_yield_pct ? `${meta.suburb_avg_yield_pct}%` : "—"} />
                          <YieldRow label="Yield index"
                            value={meta.yield_index ? `${meta.yield_index}x` : "—"}
                            highlight />
                          <YieldRow label="Rating"
                            value={yieldCfg?.label ?? "—"} />
                        </div>
                        {meta.suburb_median_sale_price && (
                          <p className="text-[10px] text-gray-400 mt-1">
                            Suburb median sale price: ${meta.suburb_median_sale_price?.toLocaleString()} ·
                            Based on {meta.comparable_rentals_found ?? "?"} comparable rentals
                          </p>
                        )}
                      </div>
                    )}

                    {/* Other metadata */}
                    {Object.keys(meta).filter(k => !YIELD_KEYS.has(k)).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(meta)
                          .filter(([k]) => !YIELD_KEYS.has(k))
                          .map(([k, v]) => (
                            <span key={k} className="text-xs bg-gray-100 rounded px-2 py-0.5">
                              <span className="text-gray-400">{k}:</span> {String(v)}
                            </span>
                          ))}
                      </div>
                    )}

                    <div className="flex items-center gap-2 pt-1">
                      {finding.url && (
                        <a href={finding.url} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                          <ExternalLink className="h-3 w-3" />
                          View listing
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

const YIELD_KEYS = new Set([
  "estimated_weekly_rent", "annual_rental_income", "rental_yield_pct",
  "suburb_avg_yield_pct", "yield_index", "yield_rating",
  "suburb_median_sale_price", "comparable_rentals_found",
]);

function YieldRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <>
      <span className="text-gray-400">{label}</span>
      <span className={highlight ? "font-semibold text-gray-800" : "text-gray-600"}>{value}</span>
    </>
  );
}
