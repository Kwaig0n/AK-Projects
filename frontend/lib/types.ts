export type AgentType = "real_estate" | "research";
export type RunStatus = "pending" | "running" | "completed" | "failed" | "stopped";
export type FindingType = "listing" | "price_change" | "research_result" | "alert";
export type LogLevel = "info" | "tool_call" | "tool_result" | "warning" | "error" | "done";

export interface Skill {
  id: string;
  name: string;
  description: string;
  icon: string;
  compatible_types: AgentType[];
}

export interface Agent {
  id: number;
  name: string;
  description: string;
  agent_type: AgentType;
  is_active: boolean;
  cron_expression: string | null;
  notify_telegram: boolean;
  telegram_chat_id: string | null;
  criteria: Record<string, unknown>;
  enabled_skills: string[];
  created_at: string;
  updated_at: string;
  last_run_status: RunStatus | null;
  last_run_at: string | null;
  last_run_id: string | null;
  next_run_at: string | null;
  findings_last_24h: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  agent_type: AgentType;
  cron_expression?: string | null;
  notify_telegram?: boolean;
  telegram_chat_id?: string | null;
  criteria: Record<string, unknown>;
  enabled_skills?: string[];
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
  cron_expression?: string | null;
  notify_telegram?: boolean;
  telegram_chat_id?: string | null;
  criteria?: Record<string, unknown>;
  enabled_skills?: string[];
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
}

export interface Run {
  id: number;
  agent_id: number;
  run_id: string;
  status: RunStatus;
  triggered_by: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  findings_count: number;
  error_message: string | null;
  tokens_used: number;
  log_entries: LogEntry[];
  agent_name: string | null;
}

export interface Finding {
  id: number;
  run_id: number;
  agent_id: number;
  title: string;
  url: string | null;
  summary: string;
  finding_type: FindingType;
  relevance_score: number;
  is_new: boolean;
  notified: boolean;
  discovered_at: string;
  metadata_json: Record<string, unknown>;
  agent_name: string | null;
}

export interface RealEstateCriteria {
  locations: string[];
  property_types: string[];
  price_min?: number;
  price_max?: number;
  bedrooms_min?: number;
  bathrooms_min?: number;
  keywords_include: string[];
  keywords_exclude: string[];
  sources: string[];
  max_results: number;
  only_new_listings: boolean;
}

export interface ResearchCriteria {
  query: string;
  search_depth: "basic" | "deep";
  max_sources: number;
  output_format: string;
  domains_include: string[];
  domains_exclude: string[];
}
