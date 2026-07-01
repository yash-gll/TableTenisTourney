import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { PlayerPicker } from "../components/PlayerPicker";
import { Button, Card, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";
import type { AdminPlayer, Match } from "../lib/types";

interface ExhibitionMatch extends Match {
  team_a_players: string[];
  team_b_players: string[];
}

const STATUS_LABEL: Record<string, string> = {
  SCHEDULED: "Not started",
  IN_PROGRESS: "Live",
  COMPLETED: "Final",
};

interface SidePlayer {
  id: string;
  name: string;
}

export function Exhibitions() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["exhibitions"],
    queryFn: () => api<ExhibitionMatch[]>("/exhibitions"),
    refetchInterval: 5000,
  });

  return (
    <AppShell title="Exhibition matches">
      <div className="space-y-4">
        <Button className="w-full" onClick={() => setCreating(true)}>
          + New exhibition
        </Button>

        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !data || data.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">
              No exhibition matches yet. Create a one-off match between any two sides — it counts
              toward Elo and skills just like a tournament match, but stays out of the tables and
              picks.
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {data.map((m) => {
              const live = m.status === "IN_PROGRESS";
              return (
                <Link key={m.id} to={`/exhibitions/${m.id}`} className="block">
                  <Card className={`active:bg-slate-50 ${live ? "border-emerald-300" : ""}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate font-medium">
                          {m.team_a_name} <span className="text-slate-400">vs</span> {m.team_b_name}
                        </div>
                        {(m.team_a_players.length > 0 || m.team_b_players.length > 0) && (
                          <div className="truncate text-xs text-slate-400">
                            {m.team_a_players.join(" & ") || "—"}{" "}
                            <span className="text-slate-300">vs</span>{" "}
                            {m.team_b_players.join(" & ") || "—"}
                          </div>
                        )}
                        {(live || m.status === "COMPLETED") && (
                          <div className="text-sm tabular-nums text-slate-600">
                            {m.team_a_score ?? 0}–{m.team_b_score ?? 0}
                          </div>
                        )}
                      </div>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                          live
                            ? "bg-emerald-100 text-emerald-700"
                            : m.status === "COMPLETED"
                              ? "bg-slate-100 text-slate-600"
                              : "bg-sky-100 text-sky-700"
                        }`}
                      >
                        {STATUS_LABEL[m.status] ?? m.status}
                      </span>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {creating && (
        <CreateExhibition
          onClose={() => setCreating(false)}
          onCreated={(matchId) => {
            queryClient.invalidateQueries({ queryKey: ["exhibitions"] });
            setCreating(false);
            navigate(`/exhibitions/${matchId}`);
          }}
        />
      )}
    </AppShell>
  );
}

function CreateExhibition({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (matchId: string) => void;
}) {
  const [aName, setAName] = useState("Team A");
  const [bName, setBName] = useState("Team B");
  const [aPlayers, setAPlayers] = useState<SidePlayer[]>([]);
  const [bPlayers, setBPlayers] = useState<SidePlayer[]>([]);
  const [targetPoints, setTargetPoints] = useState<11 | 21>(11);
  const [picking, setPicking] = useState<"A" | "B" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const assignedIds = new Set([...aPlayers, ...bPlayers].map((p) => p.id));

  const create = useMutation({
    mutationFn: () =>
      api<Match>("/exhibitions", {
        method: "POST",
        body: {
          team_a: { name: aName.trim(), player_ids: aPlayers.map((p) => p.id) },
          team_b: { name: bName.trim(), player_ids: bPlayers.map((p) => p.id) },
          target_points: targetPoints,
        },
      }),
    onSuccess: (m) => onCreated(m.id),
    onError: (e) => setError(e instanceof ApiError ? e.message : "Failed to create"),
  });

  const canSubmit =
    aName.trim() && bName.trim() && aPlayers.length >= 1 && bPlayers.length >= 1 && !create.isPending;

  const side = (
    label: "A" | "B",
    name: string,
    setName: (v: string) => void,
    players: SidePlayer[],
    setPlayers: (v: SidePlayer[]) => void,
  ) => (
    <div className="rounded-xl border border-slate-200 p-3">
      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder={`Team ${label} name`} />
      <div className="mt-2 space-y-1">
        {players.map((p) => (
          <div key={p.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span>{p.name}</span>
            <button
              onClick={() => setPlayers(players.filter((x) => x.id !== p.id))}
              className="text-rose-500"
              aria-label={`Remove ${p.name}`}
            >
              Remove
            </button>
          </div>
        ))}
        {players.length < 2 && (
          <button
            onClick={() => setPicking(label)}
            className="w-full rounded-lg border border-dashed border-slate-300 py-2 text-sm text-slate-500 active:bg-slate-50"
          >
            + Add player
          </button>
        )}
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
          <h2 className="font-semibold">New exhibition match</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">
            Cancel
          </button>
        </div>

        <div className="space-y-3">
          {side("A", aName, setAName, aPlayers, setAPlayers)}
          <div className="text-center text-xs font-medium uppercase tracking-wide text-slate-400">vs</div>
          {side("B", bName, setBName, bPlayers, setBPlayers)}
        </div>

        <div className="mt-4">
          <div className="mb-1.5 text-sm font-medium text-slate-700">Play to</div>
          <div className="flex gap-2">
            {([11, 21] as const).map((pts) => (
              <button
                key={pts}
                type="button"
                onClick={() => setTargetPoints(pts)}
                aria-pressed={targetPoints === pts}
                className={`flex-1 rounded-xl border py-3 text-sm font-semibold ${
                  targetPoints === pts
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                    : "border-slate-200 text-slate-600 active:bg-slate-50"
                }`}
              >
                {pts} points
              </button>
            ))}
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

        <Button className="mt-4 w-full" disabled={!canSubmit} onClick={() => create.mutate()}>
          {create.isPending ? "Creating…" : "Create match"}
        </Button>
      </div>

      {picking && (
        <PlayerPicker
          assignedIds={assignedIds}
          onPick={(playerId, player?: AdminPlayer) => {
            const entry = { id: playerId, name: player?.display_name ?? "Player" };
            if (picking === "A") setAPlayers([...aPlayers, entry]);
            else setBPlayers([...bPlayers, entry]);
            setPicking(null);
          }}
          onClose={() => setPicking(null)}
        />
      )}
    </div>
  );
}
