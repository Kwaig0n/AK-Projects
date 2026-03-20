"use client";
import { clsx } from "clsx";
import {
  ScheduleConfig, ScheduleType, toHuman, toCron,
  HOUR_OPTIONS, INTERVAL_OPTIONS, WEEKDAY_OPTIONS,
} from "@/lib/schedule";

const SCHEDULE_TYPES: { type: ScheduleType; label: string; description: string }[] = [
  { type: "manual",        label: "Manual only",    description: "Run by clicking Run Now or via Telegram" },
  { type: "daily",         label: "Daily",          description: "Once per day at a set time" },
  { type: "weekdays",      label: "Weekdays",       description: "Monday–Friday at a set time" },
  { type: "twice_daily",   label: "Twice daily",    description: "Two times per day" },
  { type: "every_n_hours", label: "Every N hours",  description: "Repeating interval throughout the day" },
  { type: "weekly",        label: "Weekly",         description: "Once per week on a chosen day" },
];

interface Props {
  value: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
}

export function SchedulePicker({ value, onChange }: Props) {
  function set(patch: Partial<ScheduleConfig>) {
    onChange({ ...value, ...patch });
  }

  const preview = toCron(value);

  return (
    <div className="space-y-3">
      {/* Type selector */}
      <div className="grid grid-cols-2 gap-2">
        {SCHEDULE_TYPES.map(({ type, label, description }) => (
          <button
            key={type}
            type="button"
            onClick={() => set({ type })}
            className={clsx(
              "text-left px-3 py-2.5 rounded-lg border text-sm transition-colors",
              value.type === type
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-700 border-gray-200 hover:border-blue-300"
            )}
          >
            <div className="font-medium">{label}</div>
            <div className={clsx("text-xs mt-0.5", value.type === type ? "text-blue-100" : "text-gray-400")}>
              {description}
            </div>
          </button>
        ))}
      </div>

      {/* Time/interval controls */}
      {value.type !== "manual" && value.type !== "every_n_hours" && (
        <div className="flex items-center gap-3 flex-wrap">
          {/* Weekday selector */}
          {value.type === "weekly" && (
            <div>
              <label className="text-xs text-gray-500 block mb-1">Day</label>
              <select
                value={value.weekday ?? 1}
                onChange={(e) => set({ weekday: Number(e.target.value) })}
                className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
              >
                {WEEKDAY_OPTIONS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
          )}

          {/* First hour */}
          <div>
            <label className="text-xs text-gray-500 block mb-1">
              {value.type === "twice_daily" ? "First time" : "Time"}
            </label>
            <select
              value={value.hour ?? 9}
              onChange={(e) => set({ hour: Number(e.target.value) })}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
            >
              {HOUR_OPTIONS.map((h) => (
                <option key={h.value} value={h.value}>{h.label}</option>
              ))}
            </select>
          </div>

          {/* Second hour for twice daily */}
          {value.type === "twice_daily" && (
            <div>
              <label className="text-xs text-gray-500 block mb-1">Second time</label>
              <select
                value={value.hour2 ?? 18}
                onChange={(e) => set({ hour2: Number(e.target.value) })}
                className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
              >
                {HOUR_OPTIONS.map((h) => (
                  <option key={h.value} value={h.value}>{h.label}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Interval selector */}
      {value.type === "every_n_hours" && (
        <div className="flex gap-2 flex-wrap">
          {INTERVAL_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => set({ intervalHours: opt.value })}
              className={clsx(
                "px-3 py-1.5 rounded-lg border text-sm transition-colors",
                value.intervalHours === opt.value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Preview */}
      <div className={clsx(
        "rounded-lg px-3 py-2 text-sm flex items-center justify-between",
        value.type === "manual" ? "bg-gray-50 text-gray-400" : "bg-blue-50 text-blue-700"
      )}>
        <span>{toHuman(value)}</span>
        {preview && (
          <span className="font-mono text-xs opacity-60">{preview}</span>
        )}
      </div>
    </div>
  );
}
