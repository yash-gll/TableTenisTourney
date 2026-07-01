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
import type {
  PlayerBreakdown,
  PlayerTeammates,
  PublicPlayer,
  PublicProfile,
  Teammate,
} from "../lib/types";

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
                  <Card className="flex items-center gap-2 active:bg-slate-50">
                    <span className="w-7 shrink-0 text-center">
                      {MEDALS[rank] ? (
                        <span className="text-2xl leading-none">{MEDALS[rank]}</span>
                      ) : (
                        <span className="text-sm font-semibold text-slate-400">{rank}</span>
                      )}
                    </span>
                    <Avatar name={p.display_name} size={40} />
                    {/* identity on the left, taking the slack so stats sit on the right */}
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{p.display_name}</div>
                      <div className="text-xs text-slate-400">Rating {p.current_rating}</div>
                    </div>
                    <RowStat
                      label="Won /m"
                      value={p.matches_played ? (p.rallies_won / p.matches_played).toFixed(1) : "–"}
                    />
                    <RowStat
                      label="Lost /m"
                      value={p.matches_played ? (p.rallies_lost / p.matches_played).toFixed(1) : "–"}
                    />
                    <span className="shrink-0 text-slate-300">›</span>
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

function TeammateCard({ t }: { t: Teammate }) {
  return (
    <Link
      to={`/players/${t.player_id}`}
      className="block w-full rounded-lg border border-slate-200 p-3 text-center active:bg-slate-50"
    >
      <div className="flex justify-center">
        <Avatar name={t.name} size={40} />
      </div>
      <div className="mt-1 truncate text-sm font-medium">{t.name}</div>
      <div className="text-xs text-slate-500">
        {t.wins}-{t.losses} · {t.win_pct}%
      </div>
    </Link>
  );
}

function RowStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="w-12 shrink-0 text-center leading-tight">
      <div className="text-sm font-semibold tabular-nums text-slate-700">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "text-slate-800",
}: {
  label: string;
  value: string | number;
  tone?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3 text-center shadow-sm">
      <div className={`text-xl font-bold tabular-nums ${tone}`}>{value}</div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
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
  const { data: teammates } = useQuery({
    queryKey: ["teammates", id],
    queryFn: () => api<PlayerTeammates>(`/players/${id}/teammates`),
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
        <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 p-5 text-white shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-full ring-4 ring-white/25">
              <Avatar name={profile.display_name} size={64} />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-xl font-bold">{profile.display_name}</h1>
              <div className="mt-1.5 flex flex-wrap gap-1.5 text-xs">
                <span className="rounded-full bg-white/20 px-2 py-0.5 font-medium tabular-nums">
                  Rating {profile.current_rating}
                </span>
                <span className="rounded-full bg-white/20 px-2 py-0.5 font-medium tabular-nums">
                  Peak {profile.highest_rating}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wide text-white/70">Recent form</span>
            {profile.recent_form.length ? (
              <FormPills form={profile.recent_form} />
            ) : (
              <span className="text-xs text-white/70">No matches yet</span>
            )}
          </div>
        </div>

        <AchievementBadges playerId={profile.player_id} />

        <div className="grid grid-cols-3 gap-2">
          <Stat label="Played" value={s.matches_played} />
          <Stat label="Wins" value={s.wins} tone="text-emerald-600" />
          <Stat label="Win %" value={`${s.win_pct}%`} tone="text-indigo-600" />
          <Stat label="Losses" value={s.losses} tone="text-rose-500" />
          <Stat label="Tourneys" value={s.tournaments_played} />
          <Stat label="Titles" value={s.tournament_wins} tone="text-amber-500" />
        </div>

        <RatingSparkline playerId={profile.player_id} />

        <div>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Rivalries
          </h2>
          <RivalsCard playerId={profile.player_id} />
        </div>

        {teammates && teammates.teammates.length > 0 && (
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Teammates
            </h2>
            {(() => {
              const mates = teammates.teammates;
              const top = mates[0];
              const bottom = mates[mates.length - 1];
              // Rank by win%, breaking ties by volume (more matches = more
              // trustworthy). Only a genuine tie on BOTH is unrankable.
              const distinct =
                mates.length > 1 &&
                (top.win_pct !== bottom.win_pct || top.matches !== bottom.matches);
              if (!distinct) {
                return (
                  <Card>
                    <p className="text-center text-sm text-slate-500">
                      Not enough to rank a best and worst yet — partner records are tied.
                    </p>
                  </Card>
                );
              }
              return (
                <div className="flex gap-2">
                  <div className="flex-1">
                    <div className="mb-1 text-center text-xs font-semibold uppercase text-emerald-600">
                      Best
                    </div>
                    <TeammateCard t={mates[0]} />
                  </div>
                  <div className="flex-1">
                    <div className="mb-1 text-center text-xs font-semibold uppercase text-rose-500">
                      Worst
                    </div>
                    <TeammateCard t={mates[mates.length - 1]} />
                  </div>
                </div>
              );
            })()}
          </div>
        )}

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
