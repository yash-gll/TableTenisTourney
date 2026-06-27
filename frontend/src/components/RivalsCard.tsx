import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import type { PlayerRivals } from "../lib/types";
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
    <Card className="p-0">
      {nemesis && nemesis.losses > 0 && (
        <div className="border-b border-slate-100 px-4 py-2 text-sm">
          <span className="text-slate-500">Nemesis: </span>
          <Link to={`/players/${nemesis.opponent_id}`} className="font-medium text-rose-600">
            {nemesis.opponent_name}
          </Link>
          <span className="text-slate-500"> ({nemesis.wins}–{nemesis.losses})</span>
        </div>
      )}
      <ul className="divide-y divide-slate-100">
        {top.map((r) => (
          <li key={r.opponent_id} className="flex items-center justify-between px-4 py-2.5 text-sm">
            <Link to={`/players/${r.opponent_id}`} className="font-medium">
              {r.opponent_name}
            </Link>
            <span className="tabular-nums text-slate-600">
              <span className="text-emerald-600">{r.wins}</span>–
              <span className="text-rose-500">{r.losses}</span>
              <span className="ml-1 text-xs text-slate-400">({r.meetings})</span>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
