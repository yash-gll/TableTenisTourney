import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { PlayerSkills } from "../lib/types";
import { Card } from "./ui";

function barColor(v: number): string {
  if (v >= 80) return "bg-emerald-500";
  if (v >= 60) return "bg-indigo-500";
  if (v >= 40) return "bg-amber-500";
  return "bg-rose-400";
}

export function SkillsCard({ playerId }: { playerId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["skills", playerId],
    queryFn: () => api<PlayerSkills>(`/players/${playerId}/skills`),
  });

  if (isLoading || !data) return null;

  return (
    <Card>
      <div className="space-y-3">
        {data.skills.map((s) => (
          <div key={s.key}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">{s.label}</span>
              <span className="tabular-nums text-slate-500">{s.value ?? "—"}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${s.value != null ? barColor(s.value) : ""}`}
                style={{ width: `${s.value ?? 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
