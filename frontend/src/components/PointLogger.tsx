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
type Selected = { playerId: string; playerName: string; teamId: string };

export function PointLogger({ match, teamA, teamB, targetPoints, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const [sel, setSel] = useState<Selected | null>(null);
  const [forced, setForced] = useState(false);
  const [fault, setFault] = useState<Fault | null>(null); // chosen fault, awaiting forcing skill
  const [forcerId, setForcerId] = useState<string | null>(null);
  const [pairing, setPairing] = useState<Record<string, string>>(match.serve_pairing ?? {});
  const [firstServer, setFirstServer] = useState<string | null>(match.first_server_id ?? null);
  const [setupServer, setSetupServer] = useState<string | null>(match.first_server_id ?? null);
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
  const isDoubles = (teamA?.members.length ?? 0) === 2 && (teamB?.members.length ?? 0) === 2;

  const allMembers = useMemo<TeamMember[]>(
    () => [...(teamA?.members ?? []), ...(teamB?.members ?? [])],
    [teamA, teamB],
  );
  const nameOf = (id: string | null) => allMembers.find((m) => m.player_id === id)?.display_name ?? "";
  const partnerOf = (id: string) => {
    const team = teamA?.members.some((m) => m.player_id === id) ? teamA : teamB;
    return team?.members.find((m) => m.player_id !== id)?.player_id ?? null;
  };
  const opponents = useMemo<TeamMember[]>(() => {
    if (!sel || !teamA || !teamB) return [];
    return (sel.teamId === teamA.id ? teamB : teamA).members;
  }, [sel, teamA, teamB]);

  // Whose serve it is now, and to whom. Server rotates every N points (2 to 11,
  // 5 to 21), and every point at deuce; the receiver rotates with it (ITTF
  // doubles order: server -> receiver -> server's partner -> receiver's partner).
  const serve = useMemo(() => {
    if (!firstServer || !teamA || !teamB) return null;
    const firstReceiver = pairing[firstServer] ?? partnerOf(firstServer);
    let order: string[];
    if (isDoubles && firstReceiver) {
      order = [firstServer, firstReceiver, partnerOf(firstServer), partnerOf(firstReceiver)].filter(
        Boolean,
      ) as string[];
    } else {
      order = [firstServer, allMembers.find((m) => m.player_id !== firstServer)?.player_id ?? null].filter(
        Boolean,
      ) as string[];
    }
    if (order.length < 2) return null;
    const per = targetPoints >= 21 ? 5 : 2;
    const played = a + b;
    const deuceAt = 2 * (targetPoints - 1);
    const turns = played < deuceAt ? Math.floor(played / per) : deuceAt / per + (played - deuceAt);
    return {
      server: order[turns % order.length],
      receiver: order[(turns + 1) % order.length],
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [firstServer, pairing, isDoubles, a, b, targetPoints, allMembers, teamA, teamB]);

  const refresh = () => qc.invalidateQueries({ queryKey: ["points", match.id] });
  const reset = () => {
    setSel(null);
    setForced(false);
    setFault(null);
    setForcerId(null);
  };

  const select = (m: TeamMember, teamId: string) => {
    setSel({ playerId: m.player_id, playerName: m.display_name, teamId });
    setForced(false);
    setFault(null);
  };

  const toggleForced = (on: boolean) => {
    setForced(on);
    setFault(null);
    if (on && sel) setForcerId(pairing[sel.playerId] ?? opponents[0]?.player_id ?? null);
  };

  const logPoint = async (
    playerId: string,
    skill: string,
    kind: "WIN" | "FAULT",
    forcedBy?: { forcedBy: string; forcerSkill: string },
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
          ...(forcedBy ? { forced_by: forcedBy.forcedBy, forcer_skill: forcedBy.forcerSkill } : {}),
        },
      });
      reset();
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
      const fresh = await api<Match>(`/matches/${match.id}`);
      await api(`/matches/${match.id}/points/complete?expected_version=${fresh.version}`, { method: "POST" });
      onChanged();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.code === "MATCH_VERSION_CONFLICT") onChanged();
      setError(e instanceof ApiError ? e.message : "Failed to finish match");
    } finally {
      setBusy(false);
    }
  };

  const saveServe = async (server: string, receiver: string) => {
    setError(null);
    let map: Record<string, string>;
    if (isDoubles) {
      const sp = partnerOf(server)!;
      const rp = partnerOf(receiver)!;
      map = { [server]: receiver, [receiver]: server, [sp]: rp, [rp]: sp };
    } else {
      map = { [server]: receiver, [receiver]: server };
    }
    try {
      await api(`/matches/${match.id}/serve-pairing`, {
        method: "PUT",
        body: { pairing: map, first_server_id: server },
      });
      setPairing(map);
      setFirstServer(server);
      setShowServeSetup(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to save serve setup");
    }
  };

  const chipBtn = "rounded-xl px-2 py-2.5 text-sm font-medium disabled:opacity-50";

  const teamTiles = (team: Team | undefined) =>
    team && (
      <div>
        <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">{team.name}</div>
        <div className="grid grid-cols-2 gap-2">
          {team.members.map((m) => {
            const active = sel?.playerId === m.player_id;
            return (
              <button
                key={m.player_id}
                disabled={busy}
                onClick={() => select(m, team.id)}
                className={`relative min-h-[52px] rounded-xl border px-3 py-3 text-sm font-semibold active:bg-indigo-50 disabled:opacity-40 ${
                  active ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200"
                }`}
              >
                {serve?.server === m.player_id && (
                  <span className="absolute left-2 top-2 text-xs" title="Serving">
                    🏓
                  </span>
                )}
                {serve?.receiver === m.player_id && (
                  <span className="absolute right-2 top-2 text-[10px] text-slate-400" title="Receiving">
                    ⇦
                  </span>
                )}
                {m.display_name}
              </button>
            );
          })}
        </div>
      </div>
    );

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

        <div className="mt-2 flex items-center justify-between">
          <div className="text-sm">
            {serve ? (
              <span className="font-medium text-slate-700">
                🏓 <span className="font-semibold">{nameOf(serve.server)}</span>
                <span className="text-slate-400"> → {nameOf(serve.receiver)}</span>
              </span>
            ) : (
              <span className="text-slate-400">First to {targetPoints}</span>
            )}
          </div>
          <button
            onClick={() => setShowServeSetup((v) => !v)}
            className="shrink-0 text-xs font-medium text-indigo-600"
          >
            ⚙️ Serve setup
          </button>
        </div>
        {showServeSetup && teamA && teamB && (
          <div className="mt-2 rounded-xl border border-slate-200 p-3">
            <div className="mb-1 text-xs font-medium text-slate-500">Serves first</div>
            <div className="flex flex-wrap gap-2">
              {allMembers.map((m) => (
                <button
                  key={m.player_id}
                  onClick={() => {
                    setSetupServer(m.player_id);
                    if (!isDoubles) {
                      const opp = allMembers.find((x) => x.player_id !== m.player_id);
                      if (opp) saveServe(m.player_id, opp.player_id);
                    }
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium ${
                    setupServer === m.player_id
                      ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600"
                  }`}
                >
                  {m.display_name}
                </button>
              ))}
            </div>
            {isDoubles && setupServer && (
              <>
                <div className="mb-1 mt-3 text-xs font-medium text-slate-500">
                  {nameOf(setupServer)} serves to (diagonal)
                </div>
                <div className="flex gap-2">
                  {(teamA.members.some((m) => m.player_id === setupServer) ? teamB : teamA).members.map((o) => (
                    <button
                      key={o.player_id}
                      onClick={() => saveServe(setupServer, o.player_id)}
                      className={`flex-1 rounded-lg border px-2 py-2 text-sm font-medium ${
                        pairing[setupServer] === o.player_id
                          ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                          : "border-slate-200 text-slate-600"
                      }`}
                    >
                      {o.display_name}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Players — always visible; tap one to open its action panel below */}
        <div className="mt-4 space-y-3">
          {teamTiles(teamA)}
          {teamTiles(teamB)}
        </div>

        {/* Action panel for the selected player */}
        {sel && (
          <div className="mt-3 rounded-xl border border-indigo-200 bg-indigo-50/40 p-3">
            <div className="mb-2 text-sm text-slate-600">
              <span className="font-semibold text-slate-800">{sel.playerName}</span>
            </div>

            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-600">Won with</div>
            <div className="grid grid-cols-3 gap-2">
              {SKILLS.map((sk) => (
                <button
                  key={sk.key}
                  disabled={busy}
                  onClick={() => logPoint(sel.playerId, sk.key, "WIN")}
                  className={`${chipBtn} border border-emerald-200 bg-emerald-50 text-emerald-800 active:bg-emerald-100`}
                >
                  {sk.icon} {sk.label}
                </button>
              ))}
            </div>

            <div className="mb-1 mt-4 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-rose-600">Lost by error</span>
              <div className="flex overflow-hidden rounded-full border border-slate-200 text-xs">
                <button
                  onClick={() => toggleForced(false)}
                  className={`px-3 py-1 font-medium ${!forced ? "bg-slate-700 text-white" : "text-slate-500"}`}
                >
                  Unforced
                </button>
                <button
                  onClick={() => toggleForced(true)}
                  className={`px-3 py-1 font-medium ${forced ? "bg-slate-700 text-white" : "text-slate-500"}`}
                >
                  Forced
                </button>
              </div>
            </div>

            {forced && (
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-500">Forced by</span>
                {opponents.map((o) => (
                  <button
                    key={o.player_id}
                    onClick={() => setForcerId(o.player_id)}
                    className={`rounded-full border px-2.5 py-1 text-xs font-medium ${
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

            {!forced || !fault ? (
              <div className="grid grid-cols-2 gap-2">
                {FAULTS.map((f) => (
                  <button
                    key={f.key}
                    disabled={busy}
                    onClick={() => (forced ? setFault(f) : logPoint(sel.playerId, f.key, "FAULT"))}
                    className={`${chipBtn} border border-rose-200 bg-rose-50 text-rose-700 active:bg-rose-100`}
                  >
                    {f.icon} {f.label}
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <div className="mb-1 text-xs text-slate-500">
                  {fault.label} — {nameOf(forcerId)} forced it with:
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {SKILLS.map((sk) => (
                    <button
                      key={sk.key}
                      disabled={busy || !forcerId}
                      onClick={() =>
                        forcerId &&
                        logPoint(sel.playerId, fault.key, "FAULT", {
                          forcedBy: forcerId,
                          forcerSkill: sk.key,
                        })
                      }
                      className={`${chipBtn} border border-emerald-200 bg-emerald-50 text-emerald-800 active:bg-emerald-100`}
                    >
                      {sk.icon} {sk.label}
                    </button>
                  ))}
                </div>
                <button onClick={() => setFault(null)} className="mt-2 text-xs text-slate-500">
                  ← pick a different error
                </button>
              </div>
            )}
          </div>
        )}

        {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

        <div className="mt-4 flex gap-2">
          <Button variant="secondary" className="flex-1" disabled={busy || (a === 0 && b === 0)} onClick={undo}>
            Undo
          </Button>
          <Button className="flex-1" disabled={busy || a === b} onClick={finish}>
            {a === b ? "Tied — log a point" : "Finish match"}
          </Button>
        </div>
      </div>
    </div>
  );
}
