import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Card } from "../components/ui";
import { api } from "../lib/api";
import type { HistoryDetail, HistoryItem } from "../lib/types";

interface HistoryStanding {
  rank: number;
  team_name: string;
  wins: number;
  losses: number;
  point_difference: number;
}
interface HistoryBracketMatch {
  stage: string;
  team_a: string | null;
  team_b: string | null;
  team_a_score: number | null;
  team_b_score: number | null;
}

const MEDAL = ["", "🥇", "🥈", "🥉", "4th"];

export function HistoryList() {
  const { data, isLoading } = useQuery({
    queryKey: ["history"],
    queryFn: () => api<HistoryItem[]>("/history/tournaments"),
  });

  return (
    <AppShell title="History">
      <div className="space-y-3">
        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !data || data.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">No finalized tournaments yet.</p>
          </Card>
        ) : (
          data.map((h) => (
            <Link key={h.id} to={`/history/${h.id}`} className="block">
              <Card className="active:bg-slate-50">
                <div className="font-medium">{h.name}</div>
                <div className="text-sm text-slate-500">
                  🥇 {h.champion_name ?? "—"}
                  {h.finalized_at && ` · ${new Date(h.finalized_at).toLocaleDateString()}`}
                </div>
              </Card>
            </Link>
          ))
        )}
      </div>
    </AppShell>
  );
}

export function HistoryDetailPage() {
  const { id = "" } = useParams();
  const { data: detail } = useQuery({
    queryKey: ["history", id],
    queryFn: () => api<HistoryDetail>(`/history/tournaments/${id}`),
  });
  const { data: lb } = useQuery({
    queryKey: ["history", id, "leaderboard"],
    queryFn: () => api<{ standings: HistoryStanding[] }>(`/history/tournaments/${id}/leaderboard`),
  });
  const { data: bracket } = useQuery({
    queryKey: ["history", id, "bracket"],
    queryFn: () => api<{ matches: HistoryBracketMatch[] }>(`/history/tournaments/${id}/bracket`),
  });

  if (!detail) {
    return (
      <AppShell title="History">
        <p className="text-slate-500">Loading…</p>
      </AppShell>
    );
  }

  return (
    <AppShell title={detail.name}>
      <div className="space-y-5">
        <Card className="bg-indigo-50">
          <div className="text-sm text-indigo-700">Champion</div>
          <div className="text-xl font-bold">🥇 {detail.champion_name ?? "—"}</div>
          {detail.location && <div className="mt-1 text-sm text-slate-500">📍 {detail.location}</div>}
        </Card>

        {detail.placements.length > 0 && (
          <Card>
            <h3 className="mb-2 text-sm font-semibold">Placements</h3>
            <ul className="space-y-1 text-sm">
              {detail.placements.map((p) => (
                <li key={p.team_id}>
                  {MEDAL[p.place] ?? `${p.place}th`} {p.team_name}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {lb && lb.standings.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Final group table
            </h3>
            <Card className="overflow-x-auto p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="px-3 py-2">#</th>
                    <th className="px-2 py-2">Team</th>
                    <th className="px-2 py-2 text-right">W</th>
                    <th className="px-2 py-2 text-right">L</th>
                    <th className="px-2 py-2 text-right">Diff</th>
                  </tr>
                </thead>
                <tbody>
                  {lb.standings.map((s) => (
                    <tr key={s.rank} className="border-b border-slate-100">
                      <td className="px-3 py-2 font-medium">{s.rank}</td>
                      <td className="px-2 py-2">{s.team_name}</td>
                      <td className="px-2 py-2 text-right tabular-nums">{s.wins}</td>
                      <td className="px-2 py-2 text-right tabular-nums">{s.losses}</td>
                      <td className="px-2 py-2 text-right tabular-nums">
                        {s.point_difference >= 0 ? "+" : ""}
                        {s.point_difference}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>
        )}

        {bracket && bracket.matches.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Bracket
            </h3>
            <div className="space-y-2">
              {bracket.matches.map((m, i) => (
                <Card key={i} className="flex items-center justify-between text-sm">
                  <span className="text-xs font-medium uppercase text-slate-400">{m.stage}</span>
                  <span>
                    {m.team_a ?? "—"} {m.team_a_score}–{m.team_b_score} {m.team_b ?? "—"}
                  </span>
                </Card>
              ))}
            </div>
          </div>
        )}

        <Link to="/history" className="block py-2 text-center text-sm text-slate-500">
          ← All history
        </Link>
      </div>
    </AppShell>
  );
}
