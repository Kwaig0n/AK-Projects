import { Badge } from "@/components/ui/badge";
import type { RunStatus } from "@/lib/types";
import { clsx } from "clsx";

const CONFIG: Record<RunStatus, { label: string; className: string }> = {
  pending: { label: "Pending", className: "bg-gray-100 text-gray-700 border-gray-200" },
  running: { label: "Running", className: "bg-blue-100 text-blue-700 border-blue-200 animate-pulse" },
  completed: { label: "Completed", className: "bg-green-100 text-green-700 border-green-200" },
  failed: { label: "Failed", className: "bg-red-100 text-red-700 border-red-200" },
  stopped: { label: "Stopped", className: "bg-orange-100 text-orange-700 border-orange-200" },
};

export function StatusBadge({ status }: { status: RunStatus | null }) {
  if (!status) return <span className="text-gray-400 text-sm">—</span>;
  const cfg = CONFIG[status] ?? CONFIG.pending;
  return (
    <Badge variant="outline" className={clsx("font-medium", cfg.className)}>
      {cfg.label}
    </Badge>
  );
}
