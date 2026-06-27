import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { BracketView } from "../components/BracketView";
import { LeaderboardTable } from "../components/LeaderboardTable";
import { MatchList } from "../components/MatchList";
import { PlayerPicker } from "../components/PlayerPicker";
import { PredictionLeaderboard } from "../components/PredictionLeaderboard";
import { AdminRegistrations, PlayerRegistration } from "../components/Registrations";
import { Button, Card, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type {
  Bracket,
  ExplanationResponse,
  Leaderboard,
  Match,
  MyPrediction,
  Team,
  Tournament,
  TournamentStatus,
} from "../lib/types";

type Tab = "teams" | "matches" | "table" | "bracket";

// Statuses where scores/standings can still change → auto-refresh these views.
const LIVE_STATES = ["SCHEDULED", "GROUP_IN_PROGRESS", "GROUP_COMPLETE", "QUALIFIERS_IN_PROGRESS"];
const LIVE_MS = 5000;

function manualActions(status: TournamentStatus): { label: string; target: TournamentStatus; secondary?: boolean }[] {
  switch (status) {
    case "DRAFT":
      return [{ label: "Open registration", target: "REGISTRATION_OPEN" }];
    case "REGISTRATION_OPEN":
      return [
        { label: "Lock rosters", target: "REGISTRATION_CLOSED" },
        { label: "Back to draft", target: "DRAFT", secondary: true },
      ];
    case "REGISTRATION_CLOSED":
      return [{ label: "Reopen registration", target: "REGISTRATION_OPEN", secondary: true }];
    default:
      return [];
  }
}

function defaultTab(status: TournamentStatus): Tab {
  if (status === "DRAFT" || status === "REGISTRATION_OPEN") return "teams";
  if (status === "SCHEDULED" || status === "GROUP_IN_PROGRESS") return "matches";
  if (status === "GROUP_COMPLETE") return "table";
  return "bracket";
}

export function TournamentDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const [pickingTeam, setPickingTeam] = useState<string | null>(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab | null>(null);

  const invalidate = () => {
    for (const key of ["tournament", "teams", "matches", "leaderboard", "bracket"]) {
      queryClient.invalidateQueries({ queryKey: [key, id] });
    }
  };

  const { data: t } = useQuery({
    queryKey: ["tournament", id],
    queryFn: () => api<Tournament>(`/tournaments/${id}`),
    // Poll while in progress so status changes (e.g. bracket generated) show up.
    refetchInterval: (q) =>
      LIVE_STATES.includes((q.state.data as Tournament | undefined)?.status ?? "") ? LIVE_MS : false,
  });
  const { data: teams } = useQuery({
    queryKey: ["teams", id],
    queryFn: () => api<Team[]>(`/tournaments/${id}/teams`),
  });

  const hasSchedule = t ? t.status !== "DRAFT" && t.status !== "REGISTRATION_OPEN" && t.status !== "REGISTRATION_CLOSED" : false;
  const hasBracket = t
    ? ["QUALIFIERS_IN_PROGRESS", "COMPLETED", "FINALIZED", "ARCHIVED"].includes(t.status)
    : false;
  const activeTab: Tab = tab ?? (t ? defaultTab(t.status) : "teams");
  // Live = scores/standings can still change; drives auto-refresh.
  const isLive = !!t && LIVE_STATES.includes(t.status);
  const livePoll = isLive ? LIVE_MS : false;

  const { data: matches } = useQuery({
    queryKey: ["matches", id],
    queryFn: () => api<Match[]>(`/tournaments/${id}/matches`),
    enabled: hasSchedule,
    refetchInterval: livePoll,
  });
  const { data: leaderboard } = useQuery({
    queryKey: ["leaderboard", id],
    queryFn: () => api<Leaderboard>(`/tournaments/${id}/leaderboard`),
    enabled: hasSchedule && activeTab === "table",
    refetchInterval: livePoll,
  });
  const { data: explanation } = useQuery({
    queryKey: ["leaderboard", id, "explanation"],
    queryFn: () => api<ExplanationResponse>(`/tournaments/${id}/leaderboard/explanation`),
    enabled: hasSchedule && activeTab === "table",
    refetchInterval: livePoll,
  });
  const { data: bracket } = useQuery({
    queryKey: ["bracket", id],
    queryFn: () => api<Bracket>(`/tournaments/${id}/bracket`),
    refetchInterval: livePoll,
    enabled: hasBracket && activeTab === "bracket",
  });

  // Predictions (pick'em) — players only.
  const canPredict = !isAdmin && hasSchedule;
  const { data: myPredictions } = useQuery({
    queryKey: ["predictions-me", id],
    queryFn: () => api<MyPrediction[]>(`/tournaments/${id}/predictions/me`),
    enabled: canPredict,
    refetchInterval: livePoll,
  });
  const predictionMap = Object.fromEntries(
    (myPredictions ?? []).map((p) => [p.match_id, p.predicted_winner_team_id]),
  );
  const predict = useMutation({
    mutationFn: ({ matchId, teamId }: { matchId: string; teamId: string }) =>
      api(`/matches/${matchId}/predict`, { method: "POST", body: { winner_team_id: teamId } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predictions-me", id] });
      queryClient.invalidateQueries({ queryKey: ["prediction-leaderboard", id] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Couldn't save your pick"),
  });

  const transition = useMutation({
    mutationFn: (target: TournamentStatus) =>
      api(`/tournaments/${id}/transition`, { method: "POST", body: { target } }),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Transition failed"),
  });
  const generateSchedule = useMutation({
    mutationFn: () => api(`/tournaments/${id}/schedule/generate`, { method: "POST" }),
    onSuccess: () => { setTab("matches"); invalidate(); },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Failed to generate schedule"),
  });
  const generateBracket = useMutation({
    mutationFn: () => api(`/tournaments/${id}/bracket/generate`, { method: "POST" }),
    onSuccess: () => { setTab("bracket"); invalidate(); },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Failed to generate bracket"),
  });
  const finalize = useMutation({
    mutationFn: () => api(`/tournaments/${id}/finalize`, { method: "POST" }),
    onSuccess: () => { setTab("bracket"); invalidate(); },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Failed to finalize"),
  });
  const reopen = useMutation({
    mutationFn: () => api(`/tournaments/${id}/reopen`, { method: "POST" }),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Failed to reopen"),
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

  const assignedIds = useMemo(
    () => new Set((teams ?? []).flatMap((tm) => tm.members.map((m) => m.player_id))),
    [teams],
  );

  if (!t) {
    return (
      <AppShell title="Tournament">
        <p className="text-slate-500">Loading…</p>
      </AppShell>
    );
  }

  const editable = t.is_editable;
  const tabs: { key: Tab; label: string; show: boolean }[] = [
    { key: "teams", label: "Teams", show: true },
    { key: "matches", label: "Matches", show: hasSchedule },
    { key: "table", label: "Table", show: hasSchedule },
    { key: "bracket", label: "Bracket", show: hasBracket },
  ];

  return (
    <AppShell title={t.name}>
      <div className="space-y-4">
        <Card>
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-medium text-indigo-700">
                {t.status.replace(/_/g, " ")}
              </span>
              {isLive && (
                <span className="flex items-center gap-1 text-xs font-medium text-emerald-600">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                  Live
                </span>
              )}
            </span>
            <span className="text-sm text-slate-500">
              {t.target_points} pts{t.win_by_two ? " · win by 2" : ""}
            </span>
          </div>

          {isAdmin && (
            <div className="mt-4 flex flex-wrap gap-2">
              {manualActions(t.status).map((a) => (
                <Button
                  key={a.target}
                  variant={a.secondary ? "secondary" : "primary"}
                  className="flex-1"
                  disabled={transition.isPending}
                  onClick={() => transition.mutate(a.target)}
                >
                  {a.label}
                </Button>
              ))}
              {t.status === "REGISTRATION_CLOSED" && (
                <Button className="flex-1" disabled={generateSchedule.isPending} onClick={() => generateSchedule.mutate()}>
                  Generate schedule
                </Button>
              )}
              {t.status === "GROUP_COMPLETE" && (
                <Button className="flex-1" disabled={generateBracket.isPending} onClick={() => generateBracket.mutate()}>
                  Generate bracket
                </Button>
              )}
              {t.status === "COMPLETED" && (
                <Button className="flex-1" disabled={finalize.isPending} onClick={() => finalize.mutate()}>
                  Finalize
                </Button>
              )}
              {t.status === "FINALIZED" && (
                <Button
                  variant="secondary"
                  className="flex-1"
                  disabled={reopen.isPending}
                  onClick={() => {
                    if (window.confirm("Reopen this finalized tournament? Placement bonuses will be reverted.")) {
                      reopen.mutate();
                    }
                  }}
                >
                  Reopen
                </Button>
              )}
            </div>
          )}
          {t.status === "FINALIZED" && (
            <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">
              Finalized — read-only. Results are in History.
            </p>
          )}
        </Card>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        {/* Players can request to join while registration is open. */}
        {!isAdmin && t.status === "REGISTRATION_OPEN" && <PlayerRegistration tournamentId={id} />}

        {/* Tab bar */}
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
          {tabs.filter((x) => x.show).map((x) => (
            <button
              key={x.key}
              onClick={() => setTab(x.key)}
              className={`flex-1 rounded-md py-2 text-sm font-medium ${
                activeTab === x.key ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500"
              }`}
            >
              {x.label}
            </button>
          ))}
        </div>

        {activeTab === "teams" && isAdmin && <AdminRegistrations tournamentId={id} />}

        {activeTab === "teams" && (
          <TeamsSection
            teams={teams ?? []}
            editable={editable && isAdmin}
            canRename={isAdmin && !["FINALIZED", "CANCELLED", "ARCHIVED"].includes(t.status)}
            newTeamName={newTeamName}
            setNewTeamName={setNewTeamName}
            createTeam={createTeam}
            onPick={setPickingTeam}
            renameTeam={(teamId, current) => {
              const name = window.prompt("New team name", current)?.trim();
              if (name && name !== current) {
                run(() => api(`/tournaments/${id}/teams/${teamId}`, { method: "PATCH", body: { name } }))();
              }
            }}
            removeMember={(teamId, playerId) =>
              run(() =>
                api(`/tournaments/${id}/teams/${teamId}/members/${playerId}`, { method: "DELETE" }),
              )()
            }
            deleteTeam={(teamId) =>
              run(() => api(`/tournaments/${id}/teams/${teamId}`, { method: "DELETE" }))()
            }
          />
        )}

        {activeTab === "matches" && (
          <div className="space-y-4">
            <MatchList
              matches={matches ?? []}
              targetPoints={t.target_points}
              editable={isAdmin && t.status !== "COMPLETED" && t.status !== "FINALIZED"}
              onChanged={invalidate}
              canPredict={canPredict}
              predictions={predictionMap}
              onPredict={(matchId, teamId) => predict.mutate({ matchId, teamId })}
            />
            <PredictionLeaderboard tournamentId={id} pollMs={livePoll} />
          </div>
        )}

        {activeTab === "table" && leaderboard && (
          <LeaderboardTable data={leaderboard} explanation={explanation?.explanation ?? []} />
        )}

        {activeTab === "bracket" && bracket && <BracketView data={bracket} />}

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

function TeamsSection({
  teams,
  editable,
  canRename,
  newTeamName,
  setNewTeamName,
  createTeam,
  onPick,
  renameTeam,
  removeMember,
  deleteTeam,
}: {
  teams: Team[];
  editable: boolean;
  canRename: boolean;
  newTeamName: string;
  setNewTeamName: (v: string) => void;
  createTeam: () => void;
  onPick: (teamId: string) => void;
  renameTeam: (teamId: string, currentName: string) => void;
  removeMember: (teamId: string, playerId: string) => void;
  deleteTeam: (teamId: string) => void;
}) {
  return (
    <div className="space-y-3">
      {teams.map((team) => (
        <Card key={team.id} className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="font-medium">
              {team.name}
              {team.is_complete ? (
                <span className="ml-2 text-xs font-normal text-emerald-600">complete</span>
              ) : (
                <span className="ml-2 text-xs font-normal text-amber-600">{team.members.length}/2</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {team.average_rating != null && (
                <span className="text-xs text-slate-500">avg {team.average_rating}</span>
              )}
              {canRename && (
                <button
                  onClick={() => renameTeam(team.id, team.name)}
                  className="rounded-md px-2 py-1 text-xs font-medium text-indigo-600 active:bg-indigo-50"
                >
                  Rename
                </button>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {team.members.map((m) => (
              <div key={m.player_id} className="flex items-center gap-3">
                <Avatar name={m.display_name} size={36} />
                <span className="flex-1 text-sm">{m.display_name}</span>
                <span className="text-xs text-slate-400">{m.current_rating}</span>
                {editable && (
                  <button
                    onClick={() => removeMember(team.id, m.player_id)}
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
                <Button variant="secondary" className="flex-1" onClick={() => onPick(team.id)}>
                  + Add player
                </Button>
              )}
              <button
                onClick={() => deleteTeam(team.id)}
                className="rounded-lg px-3 py-2 text-sm text-rose-600 active:bg-rose-50"
              >
                Delete
              </button>
            </div>
          )}
        </Card>
      ))}

      {editable ? (
        <Card className="flex gap-2">
          <Input placeholder="New team name" value={newTeamName} onChange={(e) => setNewTeamName(e.target.value)} />
          <Button onClick={createTeam}>Add</Button>
        </Card>
      ) : (
        teams.length === 0 && <p className="text-sm text-slate-500">No teams.</p>
      )}
    </div>
  );
}
