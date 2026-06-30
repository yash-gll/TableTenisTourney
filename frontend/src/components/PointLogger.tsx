import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError, api } from "../lib/api";
import type { Match, Team } from "../lib/types";
import { Button } from "./ui";

interface RunningScore {
  team_a: number;
  team_b: number;
}

interface Props {
  match: Match;
  teamA?: Team;
  teamB?: Team;
  targetPoints: number;
  onClose: () => void;
  onChanged: () => void;
}

// Mirror of backend app/domain/skills.py SKILL_ATTRIBUTES (order matters).
const SKILLS: { key: string; label: string; icon: string }[] = [
  { key: "serve", label: "Serve", icon: "🎯" },
  { key: "smash", label: "Smash", icon: "💥" },
  { key: "spin", label: "Spin", icon: "🌀" },
  { key: "footwork", label: "Footwork", icon: "👟" },
  { key: "consistency", label: "Consistency", icon: "🧱" },
];

export function PointLogger({ match, teamA, teamB, targetPoints, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const [pending, setPending] = useState<{ playerId: string; playerName: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: score } = useQuery({
    queryKey: ["points", match.id],
    queryFn: () => api<RunningScore>(`/matches/${match.id}/points`),
    refetchInterval: 4000,
  });

  const a = score?.team_a ?? 0;
  const b = score?.team_b ?? 0;
  const reached = a >= targetPoints || b >= targetPoints;
  const decided = a !== b && reached;

  const refresh = () => qc.invalidateQueries({ queryKey: ["points", match.id] });

  const logPoint = async (playerId: string, skill: string) => {
    setBusy(true);
    setError(null);
    try {
      await api(`/matches/${match.id}/points`, { method: "POST", body: { player_id: playerId, skill } });
      setPending(null);
      refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to log point");
    } finally {
      setBusy(false);
    }
  };

  const undo = async () => {
    setBusy(true);
    setError(null);
    try {
      await api(`/matches/${match.id}/points/last`, { method: "DELETE" });
      refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to undo");
    } finally {
      setBusy(false);
    }
  };

  const finish = async () => {
    setBusy(true);
    setError(null);
    try {
      // Logging the first point auto-starts the match and bumps its version,
      // so read the current version rather than trusting the (possibly stale) prop.
      const fresh = await api<Match>(`/matches/${match.id}`);
      await api(`/matches/${match.id}/points/complete?expected_version=${fresh.version}`, {
        method: "POST",
      });
      onChanged();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.code === "MATCH_VERSION_CONFLICT") onChanged();
      setError(e instanceof ApiError ? e.message : "Failed to finish match");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="max-h-[92vh] overflow-y-auto rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Log points</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">
            Done
          </button>
        </div>

        {/* Live score */}
        <div className="flex items-stretch gap-3">
          {[
            { name: match.team_a_name ?? "Team A", val: a, lead: a > b },
            { name: match.team_b_name ?? "Team B", val: b, lead: b > a },
          ].map((s, i) => (
            <div
              key={i}
              className={`flex-1 rounded-xl border p-3 text-center ${
                s.lead ? "border-emerald-300 bg-emerald-50" : "border-slate-200"
              }`}
            >
              <div className="mb-1 truncate text-sm font-medium text-slate-700">{s.name}</div>
              <div className="text-4xl font-bold tabular-nums">{s.val}</div>
            </div>
          ))}
        </div>
        <p className="mt-1 text-center text-xs text-slate-400">First to {targetPoints} · 11–10 counts</p>

        {/* Skill picker for the winning player, or the player grid */}
        {pending ? (
          <div className="mt-4">
            <div className="mb-2 text-sm text-slate-600">
              How did <span className="font-semibold">{pending.playerName}</span> win the rally?
            </div>
            <div className="grid grid-cols-2 gap-2">
              {SKILLS.map((sk) => (
                <button
                  key={sk.key}
                  disabled={busy}
                  onClick={() => logPoint(pending.playerId, sk.key)}
                  className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-left text-sm font-medium active:bg-slate-50 disabled:opacity-50"
                >
                  <span className="text-lg">{sk.icon}</span>
                  {sk.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setPending(null)}
              className="mt-2 w-full rounded-lg py-2 text-sm text-slate-500"
            >
              ← Back
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            <div className="text-sm text-slate-600">Tap the player who won the rally:</div>
            {[teamA, teamB].map(
              (team) =>
                team && (
                  <div key={team.id}>
                    <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                      {team.name}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {team.members.map((mem) => (
                        <button
                          key={mem.player_id}
                          disabled={busy || decided}
                          onClick={() =>
                            setPending({ playerId: mem.player_id, playerName: mem.display_name })
                          }
                          className="rounded-xl border border-slate-200 px-3 py-3 text-sm font-medium active:bg-indigo-50 disabled:opacity-40"
                        >
                          {mem.display_name}
                        </button>
                      ))}
                    </div>
                  </div>
                ),
            )}
          </div>
        )}

        {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

        <div className="mt-4 flex gap-2">
          <Button variant="secondary" className="flex-1" disabled={busy || (a === 0 && b === 0)} onClick={undo}>
            Undo
          </Button>
          <Button className="flex-1" disabled={busy || !decided} onClick={finish}>
            {decided ? "Finish match" : "Win needs a lead"}
          </Button>
        </div>
      </div>
    </div>
  );
}
