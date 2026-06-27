import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { RatingEvent } from "../lib/types";
import { Card } from "./ui";

const TYPE_LABEL: Record<string, string> = {
  MATCH_RESULT: "Match",
  TOURNAMENT_PLACEMENT_BONUS: "Placement bonus",
  ADMIN_ADJUSTMENT: "Adjustment",
};

export function RatingHistory({ playerId }: { playerId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["rating-events", playerId],
    queryFn: () => api<RatingEvent[]>(`/players/${playerId}/rating-events`),
  });

  if (isLoading) return null;
  if (!data || data.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-500">No rating changes yet — play a tournament!</p>
      </Card>
    );
  }

  const recent = [...data].reverse().slice(0, 15);
  return (
    <Card className="p-0">
      <ul className="divide-y divide-slate-100">
        {recent.map((e) => (
          <li key={e.id} className="flex items-center justify-between px-4 py-2.5">
            <div className="min-w-0">
              <div className="text-sm font-medium">{TYPE_LABEL[e.event_type] ?? e.event_type}</div>
              <div className="text-xs text-slate-400">{new Date(e.created_at).toLocaleDateString()}</div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`text-sm font-semibold tabular-nums ${
                  e.delta >= 0 ? "text-emerald-600" : "text-rose-600"
                }`}
              >
                {e.delta >= 0 ? "+" : ""}
                {e.delta}
              </span>
              <span className="w-12 text-right text-sm tabular-nums text-slate-700">
                {e.rating_after}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
