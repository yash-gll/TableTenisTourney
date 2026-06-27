import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { PredictionRow } from "../lib/types";
import { Card } from "./ui";

const MEDALS: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

export function PredictionLeaderboard({
  tournamentId,
  pollMs = false,
}: {
  tournamentId: string;
  pollMs?: number | false;
}) {
  const { data } = useQuery({
    queryKey: ["prediction-leaderboard", tournamentId],
    queryFn: () => api<PredictionRow[]>(`/tournaments/${tournamentId}/predictions/leaderboard`),
    refetchInterval: pollMs,
  });

  if (!data || data.length === 0) return null;

  return (
    <Card className="p-0">
      <div className="border-b border-slate-100 px-4 py-2 text-sm font-semibold">
        🔮 Prediction leaderboard
      </div>
      <ul className="divide-y divide-slate-100">
        {data.map((r, i) => (
          <li key={r.player_id} className="flex items-center gap-3 px-4 py-2 text-sm">
            <span className="w-5 text-center text-slate-500">{MEDALS[i + 1] ?? i + 1}</span>
            <span className="flex-1 font-medium">{r.display_name}</span>
            <span className="text-xs text-slate-400">
              {r.correct}/{r.total}
            </span>
            <span className="w-10 text-right font-semibold tabular-nums">{r.points}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
