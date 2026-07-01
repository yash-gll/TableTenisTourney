import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { ApiError, api } from "../lib/api";
import type { Match, Team, TeamMember } from "../lib/types";
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

// Mirror of backend app/domain/skills.py FAULTS.
const FAULTS: { key: string; label: string; icon: string }[] = [
  { key: "wrong_serve", label: "Wrong serve", icon: "🚫" },
  { key: "serve_net", label: "Serve into net", icon: "🕸️" },
  { key: "serve_out", label: "Serve long / out", icon: "📏" },
  { key: "hit_net", label: "Hit into net", icon: "🕸️" },
  { key: "hit_out", label: "Hit out / long", icon: "↗️" },
  { key: "out_of_position", label: "Out of position", icon: "🦶" },
];

type Fault = (typeof FAULTS)[number];

export function PointLogger({ match, teamA, teamB, targetPoints, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const [pending, setPending] = useState<{ playerId: string; playerName: string; teamId: string } | null>(null);
  const [fault, setFault] = useState<Fault | null>(null); // chosen fault, awaiting forced/unforced
  const [forcerId, setForcerId] = useState<string | null>(null);
  const [pairing, setPairing] = useState<Record<string, string>>(match.serve_pairing ?? {});
  const [showServeSetup, setShowServeSetup] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: score } = useQuery({
    queryKey: ["points", match.id],
    queryFn: () => api<RunningScore>(`/matches/${match.id}/points`),
    refetchInterval: 4000,
  });

  const a = score?.team_a ?? 0;
  const b = score?.team_b ?? 0;
  const decided = a !== b && (a >= targetPoints || b >= targetPoints);
  const isDoubles = (teamA?.members.length ?? 0) === 2 && (teamB?.members.length ?? 0) === 2;

  const opponents = useMemo<TeamMember[]>(() => {
    if (!pending || !teamA || !teamB) return [];
    return (pending.teamId === teamA.id ? teamB : teamA).members;
  }, [pending, teamA, teamB]);

  const refresh = () => qc.invalidateQueries({ queryKey: ["points", match.id] });

  const resetPicker = () => {
    setPending(null);
    setFault(null);
    setForcerId(null);
  };

  const logPoint = async (
    playerId: string,
    skill: string,
    kind: "WIN" | "FAULT",
    forced?: { forcedBy: string; forcerSkill: string },
  ) => {
    setBusy(true);
    setError(null);
    try {
      await api(`/matches/${match.id}/points`, {
        method: "POST",
        body: {
          player_id: playerId,
          skill,
          kind,
          ...(forced ? { forced_by: forced.forcedBy, forcer_skill: forced.forcerSkill } : {}),
        },
      });
      resetPicker();
      refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to log point");
    } finally {
      setBusy(false);
    }
  };

  // A fault was tapped: hold it and ask forced/unforced (default forcer from serve pairing).
  const chooseFault = (f: Fault) => {
    setFault(f);
    if (pending) setForcerId(pairing[pending.playerId] ?? opponents[0]?.player_id ?? null);
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

  const savePairing = async (map: Record<string, string>) => {
    setError(null);
    try {
      await api(`/matches/${match.id}/serve-pairing`, { method: "PUT", body: { pairing: map } });
      setPairing(map);
      setShowServeSetup(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to save serve setup");
    }
  };

  // Doubles diagonal pairing: choosing A1's opponent fixes the whole map.
  const pairingFor = (a1Opp: TeamMember): Record<string, string> => {
    const [a1, a2] = teamA!.members;
    const other = teamB!.members.find((m) => m.player_id !== a1Opp.player_id)!;
    return {
      [a1.player_id]: a1Opp.player_id,
      [a1Opp.player_id]: a1.player_id,
      [a2.player_id]: other.player_id,
      [other.player_id]: a2.player_id,
    };
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
        <p className="mt-1 text-center text-xs text-slate-400">First to {targetPoints} · {targetPoints}–{targetPoints - 1} counts</p>

        {/* Serve setup (doubles only) — sets the diagonal used to suggest the forcer */}
        {isDoubles && (
          <div className="mt-2">
            <button
              onClick={() => setShowServeSetup((v) => !v)}
              className="text-xs font-medium text-indigo-600"
            >
              ⚙️ Serve setup {Object.keys(pairing).length ? "✓" : "(who's diagonal)"}
            </button>
            {showServeSetup && teamA && teamB && (
              <div className="mt-2 rounded-xl border border-slate-200 p-3">
                <div className="mb-1 text-xs text-slate-500">
                  {teamA.members[0].display_name} serves diagonally to:
                </div>
                <div className="flex gap-2">
                  {teamB.members.map((m) => {
                    const active = pairing[teamA.members[0].player_id] === m.player_id;
                    return (
                      <button
                        key={m.player_id}
                        onClick={() => savePairing(pairingFor(m))}
                        className={`flex-1 rounded-lg border px-2 py-2 text-sm font-medium ${
                          active
                            ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                            : "border-slate-200 text-slate-600"
                        }`}
                      >
                        {m.display_name}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Forced/unforced step (a fault has been chosen) */}
        {pending && fault ? (
          <div className="mt-4">
            <div className="mb-2 text-sm">
              <span className="font-semibold">{pending.playerName}</span> — {fault.label}. Was it
              forced?
            </div>
            <button
              disabled={busy}
              onClick={() => logPoint(pending.playerId, fault.key, "FAULT")}
              className="mb-3 w-full rounded-xl border border-slate-300 px-3 py-3 text-sm font-medium active:bg-slate-50 disabled:opacity-50"
            >
              Unforced — their own mistake
            </button>

            <div className="mb-1 text-sm font-medium text-emerald-700">Forced by…</div>
            {isDoubles && (
              <div className="mb-2 flex gap-2">
                {opponents.map((o) => (
                  <button
                    key={o.player_id}
                    onClick={() => setForcerId(o.player_id)}
                    className={`flex-1 rounded-lg border px-2 py-1.5 text-xs font-medium ${
                      forcerId === o.player_id
                        ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                        : "border-slate-200 text-slate-600"
                    }`}
                  >
                    {o.display_name}
                  </button>
                ))}
              </div>
            )}
            <div className="text-xs text-slate-500">
              Tap the skill {opponents.find((o) => o.player_id === forcerId)?.display_name ?? "they"}{" "}
              forced it with:
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2">
              {SKILLS.map((sk) => (
                <button
                  key={sk.key}
                  disabled={busy || !forcerId}
                  onClick={() =>
                    forcerId &&
                    logPoint(pending.playerId, fault.key, "FAULT", {
                      forcedBy: forcerId,
                      forcerSkill: sk.key,
                    })
                  }
                  className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3 text-left text-sm font-medium text-emerald-800 active:bg-emerald-100 disabled:opacity-50"
                >
                  <span className="text-lg">{sk.icon}</span>
                  {sk.label}
                </button>
              ))}
            </div>
            <button onClick={() => setFault(null)} className="mt-2 w-full rounded-lg py-2 text-sm text-slate-500">
              ← Back
            </button>
          </div>
        ) : pending ? (
          <div className="mt-4">
            <div className="mb-2 text-sm font-medium text-emerald-700">
              <span className="font-semibold">{pending.playerName}</span> won the rally with…
            </div>
            <div className="grid grid-cols-2 gap-2">
              {SKILLS.map((sk) => (
                <button
                  key={sk.key}
                  disabled={busy}
                  onClick={() => logPoint(pending.playerId, sk.key, "WIN")}
                  className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3 text-left text-sm font-medium text-emerald-800 active:bg-emerald-100 disabled:opacity-50"
                >
                  <span className="text-lg">{sk.icon}</span>
                  {sk.label}
                </button>
              ))}
            </div>

            <div className="mb-2 mt-4 text-sm font-medium text-rose-600">…or lost the point by a fault</div>
            <div className="grid grid-cols-2 gap-2">
              {FAULTS.map((f) => (
                <button
                  key={f.key}
                  disabled={busy}
                  onClick={() => chooseFault(f)}
                  className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-3 text-left text-sm font-medium text-rose-700 active:bg-rose-100 disabled:opacity-50"
                >
                  <span className="text-lg">{f.icon}</span>
                  {f.label}
                </button>
              ))}
            </div>
            <button onClick={resetPicker} className="mt-2 w-full rounded-lg py-2 text-sm text-slate-500">
              ← Back
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            <div className="text-sm text-slate-600">Tap the player who won the rally — or made the error:</div>
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
                            setPending({
                              playerId: mem.player_id,
                              playerName: mem.display_name,
                              teamId: team.id,
                            })
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
