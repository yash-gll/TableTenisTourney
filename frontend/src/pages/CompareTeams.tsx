import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { FormPills } from "../components/FormPills";
import { ShotBreakdown } from "../components/ShotBreakdown";
import { Card } from "../components/ui";
import { api } from "../lib/api";
import type { PlayerBreakdown, PublicPlayer } from "../lib/types";
import { ComparePicker, CompareRow } from "./Compare";

interface PairStats {
  matches_played: number;
  wins: number;
  losses: number;
  win_pct: number;
  points_for: number;
  points_against: number;
}
interface MemberBreakdown {
  player_id: string;
  name: string;
  breakdown: PlayerBreakdown;
}
interface CompareSide {
  player_ids: string[];
  player_names: string[];
  avg_rating: number;
  avg_peak: number;
  stats: PairStats;
  recent_form: string[];
  skills: { key: string; label: string; value: number | null }[];
  players: MemberBreakdown[];
}
interface TeamCompareResult {
  team_a: CompareSide;
  team_b: CompareSide;
  head_to_head: { meetings: number; a_wins: number; b_wins: number };
}

function TeamBuilder({
  label,
  players,
  onAdd,
  onRemove,
}: {
  label: string;
  players: PublicPlayer[];
  onAdd: () => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="min-w-0 flex-1 rounded-xl border border-slate-200 p-3">
      <div className="mb-2 text-center text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="space-y-1.5">
        {players.map((p) => (
          <div key={p.player_id} className="flex items-center gap-2">
            <Avatar name={p.display_name} size={28} />
            <span className="min-w-0 flex-1 truncate text-sm font-medium">{p.display_name}</span>
            <button
              onClick={() => onRemove(p.player_id)}
              className="text-xs text-rose-500"
              aria-label={`Remove ${p.display_name}`}
            >
              ✕
            </button>
          </div>
        ))}
        {players.length < 2 && (
          <button
            onClick={onAdd}
            className="w-full rounded-lg border border-dashed border-slate-300 py-2 text-xs text-slate-500 active:bg-slate-50"
          >
            + Add player
          </button>
        )}
      </div>
    </div>
  );
}

export function CompareTeamsPage() {
  const [teamA, setTeamA] = useState<PublicPlayer[]>([]);
  const [teamB, setTeamB] = useState<PublicPlayer[]>([]);
  const [picking, setPicking] = useState<"a" | "b" | null>(null);

  const aIds = teamA.map((p) => p.player_id);
  const bIds = teamB.map((p) => p.player_id);
  const ready = aIds.length >= 1 && bIds.length >= 1;
  const identical =
    ready && aIds.length === bIds.length && [...aIds].sort().join() === [...bIds].sort().join();

  const { data, isFetching } = useQuery({
    queryKey: ["compare-teams", [...aIds].sort().join(","), [...bIds].sort().join(",")],
    queryFn: () =>
      api<TeamCompareResult>("/compare/teams", {
        method: "POST",
        body: { team_a: aIds, team_b: bIds },
      }),
    enabled: ready && !identical,
  });

  const add = (p: PublicPlayer) => {
    if (picking === "a") setTeamA((t) => [...t, p]);
    else setTeamB((t) => [...t, p]);
    setPicking(null);
  };

  const skillRows =
    data?.team_a.skills.map((s, i) => ({
      label: s.label,
      a: s.value,
      b: data.team_b.skills[i]?.value ?? null,
    })) ?? [];

  return (
    <AppShell title="Compare teams">
      <div className="space-y-4">
        <Card>
          <div className="flex items-stretch gap-2">
            <TeamBuilder
              label="Team A"
              players={teamA}
              onAdd={() => setPicking("a")}
              onRemove={(id) => setTeamA((t) => t.filter((p) => p.player_id !== id))}
            />
            <div className="flex items-center text-sm font-semibold text-slate-400">vs</div>
            <TeamBuilder
              label="Team B"
              players={teamB}
              onAdd={() => setPicking("b")}
              onRemove={(id) => setTeamB((t) => t.filter((p) => p.player_id !== id))}
            />
          </div>
          <p className="mt-2 text-center text-xs text-slate-400">
            Stats count only matches these players played together as this exact pair.
          </p>
        </Card>

        {!ready && (
          <p className="text-center text-sm text-slate-500">
            Build two teams (1–2 players each) to compare.
          </p>
        )}
        {identical && (
          <p className="text-center text-sm text-amber-600">Pick two different teams to compare.</p>
        )}

        {ready && !identical && isFetching && !data && (
          <p className="text-center text-sm text-slate-500">Comparing…</p>
        )}

        {data && !identical && (
          <>
            <Card>
              <div className="text-center text-xs font-semibold uppercase text-slate-500">
                Head-to-head (as pairs)
              </div>
              {data.head_to_head.meetings > 0 ? (
                <div className="mt-1 text-center text-lg font-bold tabular-nums">
                  {data.head_to_head.a_wins} <span className="text-slate-400">–</span>{" "}
                  {data.head_to_head.b_wins}
                  <div className="text-xs font-normal text-slate-500">
                    {data.head_to_head.meetings}{" "}
                    {data.head_to_head.meetings === 1 ? "meeting" : "meetings"}
                  </div>
                </div>
              ) : (
                <div className="mt-1 text-center text-sm text-slate-500">
                  These pairs haven't faced each other
                </div>
              )}
              <div className="mt-3 flex items-center justify-between">
                <FormPills form={data.team_a.recent_form} />
                <span className="text-xs uppercase text-slate-400">form</span>
                <FormPills form={data.team_b.recent_form} />
              </div>
            </Card>

            <Card className="py-1">
              <CompareRow label="Avg rating" a={data.team_a.avg_rating} b={data.team_b.avg_rating} />
              <CompareRow label="Avg peak" a={data.team_a.avg_peak} b={data.team_b.avg_peak} />
              <CompareRow
                label="Played"
                a={data.team_a.stats.matches_played}
                b={data.team_b.stats.matches_played}
              />
              <CompareRow label="Wins" a={data.team_a.stats.wins} b={data.team_b.stats.wins} />
              <CompareRow label="Win %" a={data.team_a.stats.win_pct} b={data.team_b.stats.win_pct} />
              <CompareRow
                label="Pts for"
                a={data.team_a.stats.points_for}
                b={data.team_b.stats.points_for}
              />
              <CompareRow
                label="Pts against"
                a={data.team_a.stats.points_against}
                b={data.team_b.stats.points_against}
              />
            </Card>

            <Card className="py-1">
              <div className="mb-1 pt-2 text-center text-xs font-semibold uppercase text-slate-500">
                Combined skills
              </div>
              {skillRows.map((r) => (
                <CompareRow key={r.label} label={r.label} a={r.a} b={r.b} />
              ))}
            </Card>

            {/* Per-player contribution within each pair's shared matches — who's
                carrying the team and who's dragging it. */}
            {[data.team_a, data.team_b].map((side, i) => (
              <div key={i} className="space-y-2">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {i === 0 ? "Team A" : "Team B"} — per player (as a pair)
                </h2>
                {side.players.map((p) => (
                  <Card key={p.player_id} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Avatar name={p.name} size={28} />
                      <span className="text-sm font-semibold">{p.name}</span>
                    </div>
                    <ShotBreakdown breakdown={p.breakdown} compact />
                  </Card>
                ))}
              </div>
            ))}
          </>
        )}
      </div>

      {picking && (
        <ComparePicker
          title="Add a player"
          onPick={add}
          onClose={() => setPicking(null)}
          excludeIds={new Set([...aIds, ...bIds])}
        />
      )}
    </AppShell>
  );
}
