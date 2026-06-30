import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { MatchList } from "../components/MatchList";
import { api } from "../lib/api";
import type { Match, Team, Tournament } from "../lib/types";

export function ExhibitionDetail() {
  const { matchId } = useParams<{ matchId: string }>();
  const id = matchId!;
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: match } = useQuery({
    queryKey: ["exhibition", id],
    queryFn: () => api<Match>(`/exhibitions/${id}`),
    refetchInterval: (q) => (q.state.data?.status === "COMPLETED" ? false : 4000),
  });

  const tournamentId = match?.tournament_id;
  const { data: tournament } = useQuery({
    queryKey: ["tournament", tournamentId],
    queryFn: () => api<Tournament>(`/tournaments/${tournamentId}`),
    enabled: !!tournamentId,
  });
  const { data: teams } = useQuery({
    queryKey: ["teams", tournamentId],
    queryFn: () => api<Team[]>(`/tournaments/${tournamentId}/teams`),
    enabled: !!tournamentId,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["exhibition", id] });
    queryClient.invalidateQueries({ queryKey: ["exhibitions"] });
  };

  return (
    <AppShell title="Exhibition">
      <div className="space-y-4">
        <button
          onClick={() => navigate("/exhibitions")}
          className="text-sm text-slate-500 active:text-slate-700"
        >
          ← All exhibition matches
        </button>

        {!match ? (
          <p className="text-slate-500">Loading…</p>
        ) : (
          <>
            <h2 className="text-lg font-semibold">
              {match.team_a_name} <span className="text-slate-400">vs</span> {match.team_b_name}
            </h2>
            <MatchList
              matches={[match]}
              teams={teams ?? []}
              targetPoints={tournament?.target_points ?? 11}
              editable
              onChanged={invalidate}
            />
          </>
        )}
      </div>
    </AppShell>
  );
}
