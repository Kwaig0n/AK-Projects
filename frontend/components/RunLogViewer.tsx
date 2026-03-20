"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { LogEntry, LogLevel } from "@/lib/types";
import { clsx } from "clsx";

const LEVEL_STYLES: Record<LogLevel, string> = {
  info: "text-gray-600",
  tool_call: "text-blue-600 font-medium",
  tool_result: "text-green-600",
  warning: "text-yellow-600",
  error: "text-red-600 font-medium",
  done: "text-gray-400 italic",
};

const LEVEL_BADGES: Record<LogLevel, string> = {
  info: "bg-gray-100 text-gray-500",
  tool_call: "bg-blue-100 text-blue-600",
  tool_result: "bg-green-100 text-green-600",
  warning: "bg-yellow-100 text-yellow-600",
  error: "bg-red-100 text-red-600",
  done: "bg-gray-50 text-gray-400",
};

interface Props {
  runId: string;
  initialLogs?: LogEntry[];
  isComplete?: boolean;
}

export function RunLogViewer({ runId, initialLogs = [], isComplete = false }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);
  const [streaming, setStreaming] = useState(!isComplete);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isComplete) return;

    const url = api.runs.streamUrl(runId);
    const es = new EventSource(url);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "heartbeat") return;
        setLogs((prev) => [...prev, data as LogEntry]);
        if (data.level === "done") {
          setStreaming(false);
          es.close();
        }
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setStreaming(false);
      es.close();
    };

    return () => es.close();
  }, [runId, isComplete]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span>Log</span>
        {streaming && (
          <span className="flex items-center gap-1 text-blue-500">
            <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse inline-block" />
            Live
          </span>
        )}
        <span className="ml-auto">{logs.length} entries</span>
      </div>

      <div
        ref={containerRef}
        className="h-96 overflow-y-auto rounded-lg border bg-gray-950 p-4 font-mono text-xs space-y-1"
      >
        {logs.length === 0 && (
          <div className="text-gray-500 italic">Waiting for logs...</div>
        )}
        {logs.map((entry, i) => (
          <div key={i} className={clsx("flex gap-2", LEVEL_STYLES[entry.level as LogLevel])}>
            <span className="text-gray-600 shrink-0 select-none">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span
              className={clsx(
                "shrink-0 rounded px-1 text-[10px] uppercase font-semibold leading-4",
                LEVEL_BADGES[entry.level as LogLevel]
              )}
            >
              {entry.level}
            </span>
            <span className="break-all">{entry.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
