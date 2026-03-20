/**
 * Schedule presets — each has a human label and generates a cron string.
 */

export type ScheduleType =
  | "manual"
  | "daily"
  | "weekdays"
  | "twice_daily"
  | "every_n_hours"
  | "weekly";

export interface ScheduleConfig {
  type: ScheduleType;
  hour?: number;        // 0-23, for daily/weekdays/weekly
  minute?: number;      // 0-59
  hour2?: number;       // second hour for twice_daily
  intervalHours?: number; // for every_n_hours
  weekday?: number;     // 0=Mon ... 6=Sun, for weekly
}

export const DEFAULT_SCHEDULE: ScheduleConfig = {
  type: "manual",
  hour: 9,
  minute: 0,
  hour2: 18,
  intervalHours: 4,
  weekday: 0,
};

/** Convert a ScheduleConfig to a cron expression (or null for manual). */
export function toCron(s: ScheduleConfig): string | null {
  const h = s.hour ?? 9;
  const m = s.minute ?? 0;
  switch (s.type) {
    case "manual":        return null;
    case "daily":         return `${m} ${h} * * *`;
    case "weekdays":      return `${m} ${h} * * 1-5`;
    case "twice_daily":   return `${m} ${h},${s.hour2 ?? 18} * * *`;
    case "every_n_hours": return `0 */${s.intervalHours ?? 4} * * *`;
    case "weekly":        return `${m} ${h} * * ${s.weekday ?? 1}`;
    default:              return null;
  }
}

/** Parse an existing cron string back into a ScheduleConfig (best-effort). */
export function fromCron(cron: string | null | undefined): ScheduleConfig {
  if (!cron) return { ...DEFAULT_SCHEDULE, type: "manual" };

  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return { ...DEFAULT_SCHEDULE, type: "manual" };
  const [min, hour, , , dow] = parts;

  // Every N hours: "0 */4 * * *"
  if (hour.startsWith("*/")) {
    return { ...DEFAULT_SCHEDULE, type: "every_n_hours", intervalHours: parseInt(hour.slice(2)) };
  }
  // Twice daily: "0 9,18 * * *"
  if (hour.includes(",")) {
    const [h1, h2] = hour.split(",").map(Number);
    return { ...DEFAULT_SCHEDULE, type: "twice_daily", hour: h1, hour2: h2, minute: parseInt(min) };
  }
  // Weekdays: "0 9 * * 1-5"
  if (dow === "1-5") {
    return { ...DEFAULT_SCHEDULE, type: "weekdays", hour: parseInt(hour), minute: parseInt(min) };
  }
  // Weekly: "0 9 * * 1"
  if (dow !== "*") {
    return { ...DEFAULT_SCHEDULE, type: "weekly", hour: parseInt(hour), minute: parseInt(min), weekday: parseInt(dow) };
  }
  // Daily
  return { ...DEFAULT_SCHEDULE, type: "daily", hour: parseInt(hour), minute: parseInt(min) };
}

/** Human-readable label for a ScheduleConfig. */
export function toHuman(s: ScheduleConfig | string | null | undefined): string {
  if (!s) return "Manual only";
  if (typeof s === "string") return toHuman(fromCron(s));

  const timeStr = `${String(s.hour ?? 9).padStart(2, "0")}:${String(s.minute ?? 0).padStart(2, "0")}`;
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  switch (s.type) {
    case "manual":        return "Manual only";
    case "daily":         return `Daily at ${timeStr}`;
    case "weekdays":      return `Weekdays at ${timeStr}`;
    case "twice_daily":   return `Twice daily at ${timeStr} & ${String(s.hour2 ?? 18).padStart(2, "0")}:${String(s.minute ?? 0).padStart(2, "0")}`;
    case "every_n_hours": return `Every ${s.intervalHours ?? 4} hours`;
    case "weekly":        return `Every ${DAYS[s.weekday ?? 0]} at ${timeStr}`;
    default:              return "Manual only";
  }
}

export const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => ({
  value: i,
  label: `${String(i).padStart(2, "0")}:00`,
}));

export const INTERVAL_OPTIONS = [1, 2, 3, 4, 6, 8, 12].map((n) => ({
  value: n,
  label: `Every ${n} hour${n > 1 ? "s" : ""}`,
}));

export const WEEKDAY_OPTIONS = [
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
  { value: 0, label: "Sunday" },
];
