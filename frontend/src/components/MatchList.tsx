import { useState } from "react";

import { ApiError, api } from "../lib/api";
import type { Match, MatchOdds, Team } from "../lib/types";
import { MatchScorer } from "./MatchScorer";
import { PointLogger } from "./PointLogger";
import { Button, Card } from "./ui";

interface Props {
  matches: Match[];
  targetPoints: number;
  editable: boolean;
  onChanged: () => void;
  teams?: Team[]; // needed for per-point logging (player rosters)
  // Prediction (pick'em) support — shown to players, not in admin-scoring mode.
  canPredict?: boolean;
  predictions?: Record<string, string>; // match_id -> predicted team_id
  odds?: Record<string, MatchOdds>; // match_id -> odds
  onPredict?: (matchId: string, teamId: string) => void;
}

const STATUS_LABEL: Record<string, string> = {
  WAITING_FOR_TEAMS: "Waiting",
  SCHEDULED: "Scheduled",
  IN_PROGRESS: "Live",
  COMPLETED: "Final",
};

export function MatchList({
  matches,
  targetPoints,
  editable,
  onChanged,
  teams = [],
  canPredict = false,
  predictions = {},
  odds = {},
  onPredict,
}: Props) {
  const [scoring, setScoring] = useState<{ match: Match; correct: boolean } | null>(null);
  const [logging, setLogging] = useState<Match | null>(null);
  const teamById = (id: string | null) => teams.find((t) => t.id === id);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async (m: Match) => {
    try {
      await api(`/matches/${m.id}/start`, { method: "POST" });
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed");
    }
  };

  const submit = async (a: number, b: number, reason: string) => {
    if (!scoring) return;
    setBusy(true);
    setError(null);
    const m = scoring.match;
    const path = scoring.correct ? "correct" : "complete";
    const body: Record<string, unknown> = {
      team_a_score: a,
      team_b_score: b,
      expected_version: m.version,
    };
    if (scoring.correct) body.reason = reason;
    try {
      await api(`/matches/${m.id}/${path}`, { method: "POST", body });
      setScoring(null);
      onChanged();
    } catch (e) {
      // On a version conflict refresh so the user retries against latest.
      if (e instanceof ApiError && e.code === "MATCH_VERSION_CONFLICT") onChanged();
      setError(e instanceof ApiError ? e.message : "Failed to save");
    } finally {
      setBusy(false);
    }
  };

  const winnerName = (m: Match) =>
    m.winner_team_id === m.team_a_id ? m.team_a_name : m.team_b_name;

  return (
    <div className="space-y-3">
      {error && <p className="text-sm text-rose-600">{error}</p>}
      {matches.map((m) => {
        const live = m.status === "IN_PROGRESS";
        return (
          <Card key={m.id} className={live ? "border-emerald-300" : ""}>
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-sm">
                  <span className={m.winner_team_id === m.team_a_id ? "font-semibold" : ""}>
                    {m.team_a_name ?? "TBD"}
                  </span>
                  <span className="text-slate-400">vs</span>
                  <span className={m.winner_team_id === m.team_b_id ? "font-semibold" : ""}>
                    {m.team_b_name ?? "TBD"}
                  </span>
                </div>
                {m.status === "COMPLETED" && (
                  <div className="mt-1 text-sm text-slate-600">
                    {m.team_a_score}–{m.team_b_score} · {winnerName(m)} won
                  </div>
                )}
                {live && (
                  <div className="mt-1 text-sm font-semibold tabular-nums text-emerald-700">
                    {m.team_a_score ?? 0}–{m.team_b_score ?? 0}
                  </div>
                )}
              </div>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
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

            {canPredict && m.team_a_id && m.team_b_id && (() => {
              const pick = predictions[m.id];
              const open = m.status === "SCHEDULED" || m.status === "IN_PROGRESS";
              const pickName = pick === m.team_a_id ? m.team_a_name : m.team_b_name;

              // Locked pick (already confirmed) — no changing it.
              if (open && pick) {
                return (
                  <div className="mt-2 text-xs">
                    <span className="text-slate-400">Your pick: </span>
                    <span className="font-medium">{pickName} 🔒</span>
                  </div>
                );
              }
              // No pick yet — choose, with a confirm step (final once locked).
              if (open && !pick) {
                const o = odds[m.id];
                const btn = (teamId: string, name: string | null, prob?: number, pts?: number) => (
                  <button
                    onClick={() => {
                      if (
                        window.confirm(
                          `Lock in ${name}${pts != null ? ` for +${pts} pts` : ""}? You can't change it.`,
                        )
                      ) {
                        onPredict?.(m.id, teamId);
                      }
                    }}
                    className="flex flex-1 flex-col items-center gap-0.5 rounded-md border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-600 active:bg-slate-50"
                  >
                    <span>{name}</span>
                    {prob != null && pts != null && (
                      <span className="text-[10px] font-normal text-slate-400">
                        {Math.round(prob * 100)}% · +{pts}
                      </span>
                    )}
                  </button>
                );
                return (
                  <div className="mt-3">
                    <div className="mb-1 text-xs text-slate-400">Predict the winner (final once locked)</div>
                    <div className="flex gap-2">
                      {btn(m.team_a_id, m.team_a_name, o?.team_a_prob, o?.team_a_points)}
                      {btn(m.team_b_id, m.team_b_name, o?.team_b_prob, o?.team_b_points)}
                    </div>
                  </div>
                );
              }
              if (m.status === "COMPLETED" && pick) {
                const correct = pick === m.winner_team_id;
                return (
                  <div className="mt-2 text-xs font-medium">
                    <span className={correct ? "text-emerald-600" : "text-rose-500"}>
                      {correct ? "✓ You called it" : "✗ Missed this one"} ({pickName})
                    </span>
                  </div>
                );
              }
              return null;
            })()}

            {editable && (
              <div className="mt-3 flex gap-2">
                {(m.status === "SCHEDULED" || m.status === "IN_PROGRESS") &&
                  m.team_a_id &&
                  m.team_b_id && (
                    <Button className="flex-1" onClick={() => setLogging(m)}>
                      Log points
                    </Button>
                  )}
                {m.status === "SCHEDULED" && (
                  <Button variant="secondary" className="flex-1" onClick={() => start(m)}>
                    Start
                  </Button>
                )}
                {(m.status === "SCHEDULED" || m.status === "IN_PROGRESS") && (
                  <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={() => setScoring({ match: m, correct: false })}
                  >
                    Enter result
                  </Button>
                )}
                {m.status === "COMPLETED" && (
                  <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={() => setScoring({ match: m, correct: true })}
                  >
                    Correct
                  </Button>
                )}
              </div>
            )}
          </Card>
        );
      })}

      {scoring && (
        <MatchScorer
          match={scoring.match}
          targetPoints={targetPoints}
          requireReason={scoring.correct}
          onSubmit={submit}
          onClose={() => setScoring(null)}
          busy={busy}
          error={error}
        />
      )}

      {logging && (
        <PointLogger
          match={logging}
          teamA={teamById(logging.team_a_id)}
          teamB={teamById(logging.team_b_id)}
          targetPoints={targetPoints}
          onClose={() => {
            setLogging(null);
            onChanged();
          }}
          onChanged={onChanged}
        />
      )}
    </div>
  );
}
