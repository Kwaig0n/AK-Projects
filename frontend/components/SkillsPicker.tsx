"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Skill, AgentType } from "@/lib/types";
import { clsx } from "clsx";

const ICONS: Record<string, string> = {
  newspaper: "📰",
  calculator: "🧮",
};

interface Props {
  value: string[];
  onChange: (skills: string[]) => void;
  agentType: AgentType;
}

export function SkillsPicker({ value, onChange, agentType }: Props) {
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    api.skills.list().then(setSkills).catch(() => {});
  }, []);

  const compatible = skills.filter((s) => s.compatible_types.includes(agentType));

  function toggle(id: string) {
    onChange(value.includes(id) ? value.filter((s) => s !== id) : [...value, id]);
  }

  if (compatible.length === 0) return null;

  return (
    <div className="space-y-2">
      {compatible.map((skill) => {
        const active = value.includes(skill.id);
        return (
          <label
            key={skill.id}
            className={clsx(
              "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors select-none",
              active
                ? "border-blue-300 bg-blue-50"
                : "border-gray-200 bg-white hover:border-gray-300"
            )}
          >
            <input
              type="checkbox"
              className="mt-0.5 shrink-0"
              checked={active}
              onChange={() => toggle(skill.id)}
            />
            <div>
              <div className="flex items-center gap-1.5 text-sm font-medium text-gray-800">
                <span>{ICONS[skill.icon] ?? "🔧"}</span>
                {skill.name}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">{skill.description}</p>
            </div>
          </label>
        );
      })}
    </div>
  );
}
