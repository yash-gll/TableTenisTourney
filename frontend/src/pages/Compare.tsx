import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { Card, Input } from "../components/ui";
import { api } from "../lib/api";
import type { PlayerSkills, PublicPlayer, PublicProfile } from "../lib/types";

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
  return { profile: profile.data, skills: skills.data };
}

function Picker({ onPick, onClose }: { onPick: (p: PublicPlayer) => void; onClose: () => void }) {
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: ["players-directory", q],
    queryFn: () => api<PublicPlayer[]>(`/players${q.trim() ? `?search=${encodeURIComponent(q.trim())}` : ""}`),
  });
  return (
    <div className="fixed inset-0 z-30 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="max-h-[80vh] rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Pick a player</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">Close</button>
        </div>
        <Input placeholder="Search players…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="mt-3 max-h-[55vh] space-y-1 overflow-y-auto">
          {(data ?? []).map((p) => (
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

function Row({ label, a, b }: { label: string; a: number | null; b: number | null }) {
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

  const setSlot = (slot: "a" | "b", id: string) => {
    const next = new URLSearchParams(params);
    next.set(slot, id);
    setParams(next, { replace: true });
    setPicking(null);
  };

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

        {a.profile && b.profile && (
          <>
            <Card className="py-1">
              <Row label="Rating" a={a.profile.current_rating} b={b.profile.current_rating} />
              <Row label="Peak" a={a.profile.highest_rating} b={b.profile.highest_rating} />
              <Row label="Played" a={a.profile.stats.matches_played} b={b.profile.stats.matches_played} />
              <Row label="Wins" a={a.profile.stats.wins} b={b.profile.stats.wins} />
              <Row label="Win %" a={a.profile.stats.win_pct} b={b.profile.stats.win_pct} />
              <Row label="Titles" a={a.profile.stats.tournament_wins} b={b.profile.stats.tournament_wins} />
            </Card>

            {skillRows.length > 0 && (
              <Card className="py-1">
                <div className="mb-1 pt-2 text-center text-xs font-semibold uppercase text-slate-500">
                  Skills
                </div>
                {skillRows.map((r) => (
                  <Row key={r.label} label={r.label} a={r.a} b={r.b} />
                ))}
              </Card>
            )}
          </>
        )}

        {(!a.profile || !b.profile) && (
          <p className="text-center text-sm text-slate-500">Pick two players to compare.</p>
        )}
      </div>

      {picking && (
        <Picker onPick={(p) => setSlot(picking, p.player_id)} onClose={() => setPicking(null)} />
      )}
    </AppShell>
  );
}
