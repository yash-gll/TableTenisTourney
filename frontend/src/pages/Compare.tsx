import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { FormPills } from "../components/FormPills";
import { ShotBreakdown } from "../components/ShotBreakdown";
import { Card, Input } from "../components/ui";
import { api } from "../lib/api";
import type {
  PlayerBreakdown,
  PlayerRivals,
  PlayerSkills,
  PublicPlayer,
  PublicProfile,
} from "../lib/types";

function usePlayer(id: string | null) {
  const profile = useQuery({
    queryKey: ["public-profile", id],
    queryFn: () => api<PublicProfile>(`/players/${id}`),
    enabled: !!id,
  });
  const skills = useQuery({
    queryKey: ["skills", id],
    queryFn: () => api<PlayerSkills>(`/players/${id}/skills`),
    enabled: !!id,
  });
  const breakdown = useQuery({
    queryKey: ["breakdown", id],
    queryFn: () => api<PlayerBreakdown>(`/players/${id}/breakdown`),
    enabled: !!id,
  });
  return { profile: profile.data, skills: skills.data, breakdown: breakdown.data };
}

export function ComparePicker({
  onPick,
  onClose,
  excludeIds,
  title = "Pick a player",
}: {
  onPick: (p: PublicPlayer) => void;
  onClose: () => void;
  excludeIds?: Set<string>;
  title?: string;
}) {
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: ["players-directory", q],
    queryFn: () => api<PublicPlayer[]>(`/players${q.trim() ? `?search=${encodeURIComponent(q.trim())}` : ""}`),
  });
  const players = (data ?? []).filter((p) => !excludeIds?.has(p.player_id));
  return (
    <div className="fixed inset-0 z-30 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="max-h-[80vh] rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">Close</button>
        </div>
        <Input placeholder="Search players…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="mt-3 max-h-[55vh] space-y-1 overflow-y-auto">
          {players.length === 0 && (
            <p className="py-4 text-center text-sm text-slate-500">No other players found.</p>
          )}
          {players.map((p) => (
            <button
              key={p.player_id}
              onClick={() => onPick(p)}
              className="flex w-full items-center gap-3 rounded-lg p-2 text-left active:bg-slate-100"
            >
              <Avatar name={p.display_name} size={40} />
              <span className="flex-1 font-medium">{p.display_name}</span>
              <span className="text-sm text-slate-500">{p.current_rating}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function CompareRow({ label, a, b }: { label: string; a: number | null; b: number | null }) {
  const aWins = a != null && b != null && a > b;
  const bWins = a != null && b != null && b > a;
  const cell = (v: number | null, win: boolean) => (
    <div className={`flex-1 text-center tabular-nums ${win ? "font-bold text-emerald-600" : "text-slate-700"}`}>
      {v ?? "—"}
    </div>
  );
  return (
    <div className="flex items-center border-b border-slate-100 py-2 text-sm">
      {cell(a, aWins)}
      <div className="w-28 shrink-0 text-center text-xs uppercase text-slate-400">{label}</div>
      {cell(b, bWins)}
    </div>
  );
}

function Header({
  profile,
  onChange,
}: {
  profile: PublicProfile | undefined;
  onChange: () => void;
}) {
  if (!profile) {
    return (
      <button
        onClick={onChange}
        className="flex h-full min-h-28 flex-1 flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 p-3 text-sm text-slate-500 active:bg-slate-50"
      >
        + Choose player
      </button>
    );
  }
  return (
    <button onClick={onChange} className="flex flex-1 flex-col items-center gap-1 p-2 text-center active:bg-slate-50">
      <Avatar name={profile.display_name} size={56} />
      <div className="truncate text-sm font-semibold">{profile.display_name}</div>
      <div className="text-xs text-slate-500">Rating {profile.current_rating}</div>
    </button>
  );
}

export function ComparePage() {
  const [params, setParams] = useSearchParams();
  const [picking, setPicking] = useState<"a" | "b" | null>(null);
  const aId = params.get("a");
  const bId = params.get("b");

  const a = usePlayer(aId);
  const b = usePlayer(bId);

  // Head-to-head: A's record against B (from A's rivals).
  const h2h = useQuery({
    queryKey: ["rivals", aId],
    queryFn: () => api<PlayerRivals>(`/players/${aId}/rivals`),
    enabled: !!aId && !!bId,
  });
  const record = h2h.data?.rivals.find((r) => r.opponent_id === bId);

  const setSlot = (slot: "a" | "b", id: string) => {
    const next = new URLSearchParams(params);
    next.set(slot, id);
    // Never let the same player sit in both slots.
    if ((slot === "a" && id === bId) || (slot === "b" && id === aId)) {
      next.delete(slot === "a" ? "b" : "a");
    }
    setParams(next, { replace: true });
    setPicking(null);
  };

  const samePlayer = !!aId && aId === bId;

  const skillRows =
    a.skills && b.skills
      ? a.skills.skills.map((s, i) => ({
          label: s.label,
          a: s.value,
          b: b.skills!.skills[i]?.value ?? null,
        }))
      : [];

  return (
    <AppShell title="Compare">
      <div className="space-y-4">
        <Card>
          <div className="flex items-stretch gap-2">
            <Header profile={a.profile} onChange={() => setPicking("a")} />
            <div className="flex items-center text-sm font-semibold text-slate-400">vs</div>
            <Header profile={b.profile} onChange={() => setPicking("b")} />
          </div>
        </Card>

        {samePlayer && (
          <p className="text-center text-sm text-amber-600">
            Pick two different players to compare.
          </p>
        )}

        {a.profile && b.profile && !samePlayer && (
          <>
            <Card>
              <div className="text-center text-xs font-semibold uppercase text-slate-500">
                Head-to-head
              </div>
              {record ? (
                <div className="mt-1 text-center text-lg font-bold tabular-nums">
                  {record.wins} <span className="text-slate-400">–</span> {record.losses}
                  <div className="text-xs font-normal text-slate-500">
                    {record.meetings} {record.meetings === 1 ? "meeting" : "meetings"}
                  </div>
                </div>
              ) : (
                <div className="mt-1 text-center text-sm text-slate-500">Haven't played yet</div>
              )}
              <div className="mt-3 flex items-center justify-between">
                <FormPills form={a.profile.recent_form} />
                <span className="text-xs uppercase text-slate-400">form</span>
                <FormPills form={b.profile.recent_form} />
              </div>
            </Card>

            <Card className="py-1">
              <CompareRow label="Rating" a={a.profile.current_rating} b={b.profile.current_rating} />
              <CompareRow label="Peak" a={a.profile.highest_rating} b={b.profile.highest_rating} />
              <CompareRow label="Played" a={a.profile.stats.matches_played} b={b.profile.stats.matches_played} />
              <CompareRow label="Wins" a={a.profile.stats.wins} b={b.profile.stats.wins} />
              <CompareRow label="Win %" a={a.profile.stats.win_pct} b={b.profile.stats.win_pct} />
              <CompareRow label="Titles" a={a.profile.stats.tournament_wins} b={b.profile.stats.tournament_wins} />
            </Card>

            {skillRows.length > 0 && (
              <Card className="py-1">
                <div className="mb-1 pt-2 text-center text-xs font-semibold uppercase text-slate-500">
                  Skills
                </div>
                {skillRows.map((r) => (
                  <CompareRow key={r.label} label={r.label} a={r.a} b={r.b} />
                ))}
              </Card>
            )}

            {a.breakdown && b.breakdown && (
              <Card className="space-y-3">
                <div className="text-center text-xs font-semibold uppercase text-slate-500">
                  Shot breakdown
                </div>
                <div>
                  <div className="mb-1 text-sm font-semibold">{a.profile.display_name}</div>
                  <ShotBreakdown breakdown={a.breakdown} compact />
                </div>
                <hr className="border-slate-100" />
                <div>
                  <div className="mb-1 text-sm font-semibold">{b.profile.display_name}</div>
                  <ShotBreakdown breakdown={b.breakdown} compact />
                </div>
              </Card>
            )}
          </>
        )}

        {(!a.profile || !b.profile) && (
          <p className="text-center text-sm text-slate-500">Pick two players to compare.</p>
        )}
      </div>

      {picking && (
        <ComparePicker
          onPick={(p) => setSlot(picking, p.player_id)}
          onClose={() => setPicking(null)}
          excludeIds={new Set([picking === "a" ? bId : aId].filter(Boolean) as string[])}
        />
      )}
    </AppShell>
  );
}
