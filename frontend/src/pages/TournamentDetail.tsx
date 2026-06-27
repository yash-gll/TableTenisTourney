import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { PlayerPicker } from "../components/PlayerPicker";
import { Button, Card, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";
import type { Team, Tournament, TournamentStatus } from "../lib/types";

interface Action {
  label: string;
  target: TournamentStatus;
  variant?: "primary" | "secondary" | "danger";
  confirm?: string;
}

function actionsFor(status: TournamentStatus): Action[] {
  switch (status) {
    case "DRAFT":
      return [{ label: "Open registration", target: "REGISTRATION_OPEN" }];
    case "REGISTRATION_OPEN":
      return [
        { label: "Lock rosters", target: "REGISTRATION_CLOSED" },
        { label: "Back to draft", target: "DRAFT", variant: "secondary" },
      ];
    case "REGISTRATION_CLOSED":
      return [{ label: "Reopen registration", target: "REGISTRATION_OPEN", variant: "secondary" }];
    default:
      return [];
  }
}

export function TournamentDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pickingTeam, setPickingTeam] = useState<string | null>(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["tournament", id] });
    queryClient.invalidateQueries({ queryKey: ["teams", id] });
  };

  const { data: t } = useQuery({
    queryKey: ["tournament", id],
    queryFn: () => api<Tournament>(`/tournaments/${id}`),
  });
  const { data: teams } = useQuery({
    queryKey: ["teams", id],
    queryFn: () => api<Team[]>(`/tournaments/${id}/teams`),
  });

  const run = <T,>(fn: () => Promise<T>) => async () => {
    setError(null);
    try {
      await fn();
      invalidate();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong");
    }
  };

  const transition = useMutation({
    mutationFn: (target: TournamentStatus) =>
      api(`/tournaments/${id}/transition`, { method: "POST", body: { target } }),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Transition failed"),
  });

  const createTeam = run(async () => {
    if (!newTeamName.trim()) return;
    await api(`/tournaments/${id}/teams`, { method: "POST", body: { name: newTeamName.trim() } });
    setNewTeamName("");
  });

  const addMember = async (teamId: string, playerId: string) => {
    setPickingTeam(null);
    await run(() =>
      api(`/tournaments/${id}/teams/${teamId}/members`, { method: "POST", body: { player_id: playerId } }),
    )();
  };

  if (!t) {
    return (
      <AppShell title="Tournament">
        <p className="text-slate-500">Loading…</p>
      </AppShell>
    );
  }

  const editable = t.is_editable;
  const assignedIds = new Set((teams ?? []).flatMap((tm) => tm.members.map((m) => m.player_id)));

  return (
    <AppShell title={t.name}>
      <div className="space-y-5">
        <Card>
          <div className="flex items-center justify-between gap-2">
            <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-medium text-indigo-700">
              {t.status.replace(/_/g, " ")}
            </span>
            <span className="text-sm text-slate-500">
              {t.target_points} pts{t.win_by_two ? " · win by 2" : ""}
            </span>
          </div>
          {t.location && <p className="mt-2 text-sm text-slate-600">📍 {t.location}</p>}

          <div className="mt-4 flex flex-wrap gap-2">
            {actionsFor(t.status).map((a) => (
              <Button
                key={a.target}
                variant={a.variant ?? "primary"}
                className="flex-1"
                disabled={transition.isPending}
                onClick={() => transition.mutate(a.target)}
              >
                {a.label}
              </Button>
            ))}
          </div>
        </Card>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Teams ({teams?.length ?? 0})
          </h2>

          {(teams ?? []).map((team) => (
            <Card key={team.id} className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="font-medium">
                  {team.name}
                  {team.is_complete ? (
                    <span className="ml-2 text-xs font-normal text-emerald-600">complete</span>
                  ) : (
                    <span className="ml-2 text-xs font-normal text-amber-600">
                      {team.members.length}/2
                    </span>
                  )}
                </div>
                {team.average_rating != null && (
                  <span className="text-xs text-slate-500">avg {team.average_rating}</span>
                )}
              </div>

              <div className="space-y-2">
                {team.members.map((m) => (
                  <div key={m.player_id} className="flex items-center gap-3">
                    <Avatar name={m.display_name} size={36} />
                    <span className="flex-1 text-sm">{m.display_name}</span>
                    <span className="text-xs text-slate-400">{m.current_rating}</span>
                    {editable && (
                      <button
                        onClick={run(() =>
                          api(`/tournaments/${id}/teams/${team.id}/members/${m.player_id}`, {
                            method: "DELETE",
                          }),
                        )}
                        className="rounded-md px-2 py-1 text-xs text-rose-600 active:bg-rose-50"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {editable && (
                <div className="flex gap-2">
                  {team.members.length < 2 && (
                    <Button variant="secondary" className="flex-1" onClick={() => setPickingTeam(team.id)}>
                      + Add player
                    </Button>
                  )}
                  <button
                    onClick={run(() =>
                      api(`/tournaments/${id}/teams/${team.id}`, { method: "DELETE" }),
                    )}
                    className="rounded-lg px-3 py-2 text-sm text-rose-600 active:bg-rose-50"
                  >
                    Delete team
                  </button>
                </div>
              )}
            </Card>
          ))}

          {editable ? (
            <Card className="flex gap-2">
              <Input
                placeholder="New team name"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
              />
              <Button onClick={createTeam}>Add</Button>
            </Card>
          ) : (
            <p className="text-sm text-slate-500">Rosters are locked in this state.</p>
          )}
        </div>

        {editable && (
          <button
            onClick={() => {
              if (window.confirm("Cancel this tournament? This cannot be undone.")) {
                transition.mutate("CANCELLED");
              }
            }}
            className="w-full rounded-lg py-3 text-sm font-medium text-rose-600 active:bg-rose-50"
          >
            Cancel tournament
          </button>
        )}

        <button
          onClick={() => navigate("/tournaments")}
          className="w-full rounded-lg py-2 text-sm text-slate-500"
        >
          ← All tournaments
        </button>
      </div>

      {pickingTeam && (
        <PlayerPicker
          assignedIds={assignedIds}
          onPick={(playerId) => addMember(pickingTeam, playerId)}
          onClose={() => setPickingTeam(null)}
        />
      )}
    </AppShell>
  );
}
