import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Card } from "../components/ui";
import { api } from "../lib/api";
import type { LiveMatch } from "../lib/types";

interface SpectatorBoard {
  live: LiveMatch[];
  upcoming: LiveMatch[];
  recent: LiveMatch[];
}

function MatchCard({ m, kind, onOpen }: { m: LiveMatch; kind: "live" | "upcoming" | "recent"; onOpen?: () => void }) {
  const clickable = !m.is_exhibition && !!onOpen;
  const winnerA = m.winner_name && m.winner_name === m.team_a_name;
  const winnerB = m.winner_name && m.winner_name === m.team_b_name;
  return (
    <Card
      className={`${kind === "live" ? "border-emerald-300" : ""} ${clickable ? "active:bg-slate-50" : ""}`}
      onClick={clickable ? onOpen : undefined}
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="truncate text-xs font-medium uppercase tracking-wide text-slate-400">
          {m.context_name}
        </span>
        {kind === "live" && (
          <span className="flex shrink-0 items-center gap-1 text-xs font-semibold text-emerald-600">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            LIVE
          </span>
        )}
        {kind === "upcoming" && (
          <span className="shrink-0 text-xs font-medium text-sky-600">Up next</span>
        )}
        {kind === "recent" && <span className="shrink-0 text-xs font-medium text-slate-400">Final</span>}
      </div>
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className={`truncate text-sm ${winnerA ? "font-bold" : "font-medium"}`}>
            {m.team_a_name ?? "TBD"}
          </div>
          <div className={`truncate text-sm ${winnerB ? "font-bold" : "font-medium"}`}>
            {m.team_b_name ?? "TBD"}
          </div>
        </div>
        {kind !== "upcoming" && (
          <div className="shrink-0 text-right tabular-nums">
            <div className={`text-2xl leading-tight ${winnerA ? "font-extrabold" : "font-bold"}`}>
              {m.team_a_score ?? 0}
            </div>
            <div className={`text-2xl leading-tight ${winnerB ? "font-extrabold" : "font-bold"}`}>
              {m.team_b_score ?? 0}
            </div>
          </div>
        )}
      </div>
      {kind === "live" && (
        <div className="mt-1 text-right text-xs text-slate-400">first to {m.target_points}</div>
      )}
    </Card>
  );
}

function Section({
  title,
  items,
  kind,
  onOpen,
}: {
  title: string;
  items: LiveMatch[];
  kind: "live" | "upcoming" | "recent";
  onOpen: (m: LiveMatch) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h2>
      {items.map((m) => (
        <MatchCard key={m.id} m={m} kind={kind} onOpen={() => onOpen(m)} />
      ))}
    </div>
  );
}

export function LivePage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["live"],
    queryFn: () => api<SpectatorBoard>("/live"),
    refetchInterval: 4000,
  });

  const open = (m: LiveMatch) => navigate(`/tournaments/${m.tournament_id}`);
  const empty = data && !data.live.length && !data.upcoming.length && !data.recent.length;

  return (
    <AppShell title="Live">
      <div className="space-y-5">
        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : empty ? (
          <Card>
            <p className="text-sm text-slate-500">
              Nothing happening right now. Matches show up here the moment someone starts scoring.
            </p>
          </Card>
        ) : (
          <>
            <Section title="Live now" items={data!.live} kind="live" onOpen={open} />
            <Section title="Up next" items={data!.upcoming} kind="upcoming" onOpen={open} />
            <Section title="Recently finished" items={data!.recent} kind="recent" onOpen={open} />
          </>
        )}
      </div>
    </AppShell>
  );
}
