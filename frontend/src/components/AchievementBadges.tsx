import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { PlayerAchievements } from "../lib/types";

export function AchievementBadges({ playerId }: { playerId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["achievements", playerId],
    queryFn: () => api<PlayerAchievements>(`/players/${playerId}/achievements`),
  });

  if (isLoading || !data) return null;
  if (data.achievements.length === 0) {
    return <p className="text-sm text-slate-400">No badges yet — win some matches!</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {data.achievements.map((b) => (
        <span
          key={b.key}
          title={b.description}
          className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium shadow-sm"
        >
          <span aria-hidden>{b.icon}</span>
          {b.label}
        </span>
      ))}
    </div>
  );
}
