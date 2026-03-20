"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SchedulePicker } from "@/components/SchedulePicker";
import { toCron, fromCron, DEFAULT_SCHEDULE } from "@/lib/schedule";
import type { ScheduleConfig } from "@/lib/schedule";
import { api } from "@/lib/api";
import type { AgentType } from "@/lib/types";

const DEFAULT_RE_CRITERIA = {
  locations: ["Sydney CBD"],
  property_types: ["apartment", "house"],
  price_min: 500000,
  price_max: 1000000,
  bedrooms_min: 2,
  bathrooms_min: 1,
  keywords_include: [],
  keywords_exclude: [],
  sources: ["domain.com.au", "realestate.com.au"],
  max_results: 20,
  only_new_listings: true,
};

const DEFAULT_RESEARCH_CRITERIA = {
  query: "",
  search_depth: "basic",
  max_sources: 10,
  output_format: "summary",
  domains_include: [],
  domains_exclude: [],
};

export default function NewAgentPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    agent_type: "real_estate" as AgentType,
    notify_telegram: true,
  });
  const [schedule, setSchedule] = useState<ScheduleConfig>({ ...DEFAULT_SCHEDULE, type: "manual" });
  const [criteriaStr, setCriteriaStr] = useState(JSON.stringify(DEFAULT_RE_CRITERIA, null, 2));
  const [criteriaError, setCriteriaError] = useState("");

  function handleTypeChange(t: AgentType) {
    setForm((f) => ({ ...f, agent_type: t }));
    setCriteriaStr(JSON.stringify(
      t === "real_estate" ? DEFAULT_RE_CRITERIA : DEFAULT_RESEARCH_CRITERIA, null, 2
    ));
    setCriteriaError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    let criteria: Record<string, unknown>;
    try {
      criteria = JSON.parse(criteriaStr);
      setCriteriaError("");
    } catch {
      setCriteriaError("Invalid JSON — please fix before saving.");
      return;
    }
    setSaving(true);
    try {
      const agent = await api.agents.create({
        name: form.name,
        description: form.description,
        agent_type: form.agent_type,
        cron_expression: toCron(schedule),
        notify_telegram: form.notify_telegram,
        criteria,
      });
      router.push(`/agents/${agent.id}`);
    } catch (err) {
      alert(`Failed to create agent: ${err}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-6 max-w-2xl space-y-4">
      <Link href="/agents" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Agents
      </Link>
      <h1 className="text-2xl font-bold text-gray-900">New Agent</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card>
          <CardHeader><CardTitle className="text-base">Basic Info</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Agent Name *</Label>
              <Input id="name" required value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Sydney Property Monitor" />
            </div>
            <div>
              <Label htmlFor="desc">Description</Label>
              <Input id="desc" value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Optional short description" />
            </div>
            <div>
              <Label>Agent Type *</Label>
              <div className="flex gap-2 mt-1">
                {(["real_estate", "research"] as AgentType[]).map((t) => (
                  <button key={t} type="button" onClick={() => handleTypeChange(t)}
                    className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                      form.agent_type === t
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
                    }`}>
                    {t === "real_estate" ? "🏠 Real Estate" : "🔍 Research"}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Schedule</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <SchedulePicker value={schedule} onChange={setSchedule} />
            <div className="flex items-center gap-2 pt-1">
              <input type="checkbox" id="tg" checked={form.notify_telegram}
                onChange={(e) => setForm((f) => ({ ...f, notify_telegram: e.target.checked }))} />
              <Label htmlFor="tg">Send Telegram notifications when findings are ready</Label>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Search Criteria (JSON)</CardTitle></CardHeader>
          <CardContent>
            <Textarea value={criteriaStr} onChange={(e) => setCriteriaStr(e.target.value)}
              className="font-mono text-xs h-64" />
            {criteriaError && <p className="text-red-500 text-xs mt-1">{criteriaError}</p>}
          </CardContent>
        </Card>

        <div className="flex gap-2 justify-end">
          <Link href="/agents"><Button variant="outline" type="button">Cancel</Button></Link>
          <Button type="submit" disabled={saving}>{saving ? "Creating..." : "Create Agent"}</Button>
        </div>
      </form>
    </div>
  );
}
