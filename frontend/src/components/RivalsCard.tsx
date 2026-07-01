import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import type { PlayerRivals } from "../lib/types";
import { Avatar } from "./Avatar";
import { Card } from "./ui";

export function RivalsCard({ playerId }: { playerId: string }) {
  const { data } = useQuery({
    queryKey: ["rivals", playerId],
    queryFn: () => api<PlayerRivals>(`/players/${playerId}/rivals`),
  });

  if (!data || data.rivals.length === 0) return null;

  const top = data.rivals.slice(0, 5);
  // Nemesis = the opponent who's beaten them the most.
  const nemesis = [...data.rivals].sort((a, b) => b.losses - a.losses)[0];

  return (
    <Card className="overflow-hidden p-0">
      {nemesis && nemesis.losses > 0 && (
        <Link
          to={`/players/${nemesis.opponent_id}`}
          className="flex items-center gap-2 border-b border-slate-100 bg-rose-50 px-4 py-2.5 active:bg-rose-100"
        >
          <span className="text-lg">😈</span>
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-rose-400">
              Nemesis
            </div>
            <div className="truncate text-sm font-semibold text-rose-600">
              {nemesis.opponent_name}
            </div>
          </div>
          <span className="shrink-0 text-sm font-bold tabular-nums text-rose-600">
            {nemesis.wins}–{nemesis.losses}
          </span>
        </Link>
      )}
      <ul className="divide-y divide-slate-100">
        {top.map((r) => {
          const winPct = r.meetings ? Math.round((r.wins / r.meetings) * 100) : 0;
          return (
            <li key={r.opponent_id}>
              <Link
                to={`/players/${r.opponent_id}`}
                className="flex items-center gap-3 px-4 py-2.5 active:bg-slate-50"
              >
                <Avatar name={r.opponent_name} size={32} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{r.opponent_name}</div>
                  <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-slate-100">
                    <div className="bg-emerald-400" style={{ width: `${winPct}%` }} />
                    <div className="bg-rose-400" style={{ width: `${100 - winPct}%` }} />
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-sm font-semibold tabular-nums">
                    <span className="text-emerald-600">{r.wins}</span>
                    <span className="text-slate-300">–</span>
                    <span className="text-rose-500">{r.losses}</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {r.meetings} {r.meetings === 1 ? "meeting" : "meetings"}
                  </div>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
