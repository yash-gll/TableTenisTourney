import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Card } from "../components/ui";
import { api } from "../lib/api";
import type { LiveMatch } from "../lib/types";

export function LivePage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["live"],
    queryFn: () => api<LiveMatch[]>("/live"),
    refetchInterval: 4000,
  });

  return (
    <AppShell title="Live now">
      <div className="space-y-3">
        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !data || data.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">
              Nothing live right now. Matches show up here the moment someone starts scoring.
            </p>
          </Card>
        ) : (
          data.map((m) => {
            // Tournament matches open the (read-only) tournament; exhibitions have
            // no player-facing page, so their score just shows here.
            const clickable = !m.is_exhibition;
            return (
              <Card
                key={m.id}
                className={`border-emerald-300 ${clickable ? "active:bg-slate-50" : ""}`}
                onClick={clickable ? () => navigate(`/tournaments/${m.tournament_id}`) : undefined}
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="truncate text-xs font-medium uppercase tracking-wide text-slate-400">
                    {m.context_name}
                  </span>
                  <span className="flex shrink-0 items-center gap-1 text-xs font-semibold text-emerald-600">
                    <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                    LIVE
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{m.team_a_name ?? "TBD"}</div>
                    <div className="truncate text-sm font-medium">{m.team_b_name ?? "TBD"}</div>
                  </div>
                  <div className="shrink-0 text-right tabular-nums">
                    <div className="text-2xl font-bold leading-tight">{m.team_a_score ?? 0}</div>
                    <div className="text-2xl font-bold leading-tight">{m.team_b_score ?? 0}</div>
                  </div>
                </div>
                <div className="mt-1 text-right text-xs text-slate-400">first to {m.target_points}</div>
              </Card>
            );
          })
        )}
      </div>
    </AppShell>
  );
}
