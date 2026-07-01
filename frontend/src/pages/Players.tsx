import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { AchievementBadges } from "../components/AchievementBadges";
import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { FormPills } from "../components/FormPills";
import { RatingSparkline } from "../components/RatingSparkline";
import { RivalsCard } from "../components/RivalsCard";
import { ShotBreakdown } from "../components/ShotBreakdown";
import { SkillsCard } from "../components/SkillsCard";
import { Card, Input } from "../components/ui";

const MEDALS: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { PlayerBreakdown, PublicPlayer, PublicProfile } from "../lib/types";

export function PlayersDirectory() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["players-directory", q],
    queryFn: () => api<PublicPlayer[]>(`/players${q.trim() ? `?search=${encodeURIComponent(q.trim())}` : ""}`),
  });

  return (
    <AppShell title="Players">
      <div className="space-y-4">
        {isAdmin && (
          <button
            onClick={() => navigate("/admin")}
            className="w-full rounded-lg border border-slate-200 py-2 text-sm font-medium text-indigo-700 active:bg-slate-50"
          >
            Manage approvals & skills →
          </button>
        )}
        <div className="flex gap-2">
          <button
            onClick={() => navigate("/players/compare")}
            className="flex-1 rounded-lg border border-slate-200 py-2 text-sm font-medium text-indigo-700 active:bg-slate-50"
          >
            ⚖️ Compare players
          </button>
          <button
            onClick={() => navigate("/players/compare-teams")}
            className="flex-1 rounded-lg border border-slate-200 py-2 text-sm font-medium text-indigo-700 active:bg-slate-50"
          >
            👥 Compare teams
          </button>
        </div>
        <Input placeholder="Search players by name…" value={q} onChange={(e) => setQ(e.target.value)} />

        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !data || data.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">No players found.</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {data.map((p, i) => {
              const rank = i + 1;
              return (
                <Link key={p.player_id} to={`/players/${p.player_id}`} className="block">
                  <Card className="flex items-center gap-3 active:bg-slate-50">
                    <span className="w-6 shrink-0 text-center text-sm font-semibold text-slate-500">
                      {MEDALS[rank] ?? rank}
                    </span>
                    <Avatar name={p.display_name} size={44} />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium">{p.display_name}</div>
                      <div className="text-sm text-slate-500">Rating {p.current_rating}</div>
                      {p.matches_played > 0 ? (
                        <div className="text-xs text-slate-400">
                          {p.matches_played} played · {p.win_pct}% W ·{" "}
                          {Math.round(100 - p.win_pct)}% L
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400">No matches yet</div>
                      )}
                    </div>
                    <span className="text-slate-300">›</span>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-center">
      <div className="text-lg font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

export function PublicProfilePage() {
  const { id = "" } = useParams();
  const { data: profile } = useQuery({
    queryKey: ["public-profile", id],
    queryFn: () => api<PublicProfile>(`/players/${id}`),
  });
  const { data: breakdown } = useQuery({
    queryKey: ["breakdown", id],
    queryFn: () => api<PlayerBreakdown>(`/players/${id}/breakdown`),
  });

  if (!profile) {
    return (
      <AppShell title="Player">
        <p className="text-slate-500">Loading…</p>
      </AppShell>
    );
  }

  const s = profile.stats;
  return (
    <AppShell title={profile.display_name}>
      <div className="space-y-5">
        <div className="flex items-center gap-4">
          <Avatar name={profile.display_name} size={64} />
          <div>
            <h1 className="text-xl font-semibold">{profile.display_name}</h1>
            <p className="text-sm text-slate-500">
              Rating {profile.current_rating} · peak {profile.highest_rating}
            </p>
          </div>
        </div>

        <AchievementBadges playerId={profile.player_id} />

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-500">Recent form</span>
          <FormPills form={profile.recent_form} />
        </div>

        <div className="grid grid-cols-3 gap-2">
          <Stat label="Played" value={s.matches_played} />
          <Stat label="Wins" value={s.wins} />
          <Stat label="Win %" value={`${s.win_pct}%`} />
          <Stat label="Losses" value={s.losses} />
          <Stat label="Tourneys" value={s.tournaments_played} />
          <Stat label="Titles" value={s.tournament_wins} />
        </div>

        <RatingSparkline playerId={profile.player_id} />

        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Rivalries
          </h2>
          <RivalsCard playerId={profile.player_id} />
        </div>

        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Skills</h2>
          <SkillsCard playerId={profile.player_id} />
        </div>

        {breakdown && (
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Shot breakdown
            </h2>
            <Card>
              <ShotBreakdown breakdown={breakdown} />
            </Card>
          </div>
        )}

        <Link
          to={`/players/compare?a=${profile.player_id}`}
          className="block rounded-lg border border-slate-200 py-2 text-center text-sm font-medium text-indigo-700 active:bg-slate-50"
        >
          ⚖️ Compare with another player
        </Link>
        <Link to="/players" className="block py-2 text-center text-sm text-slate-500">
          ← All players
        </Link>
      </div>
    </AppShell>
  );
}
