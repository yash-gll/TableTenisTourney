import { useState } from "react";

import { ApiError, api } from "../lib/api";
import type { Match } from "../lib/types";
import { MatchScorer } from "./MatchScorer";
import { Button, Card } from "./ui";

interface Props {
  matches: Match[];
  targetPoints: number;
  editable: boolean;
  onChanged: () => void;
}

const STATUS_LABEL: Record<string, string> = {
  WAITING_FOR_TEAMS: "Waiting",
  SCHEDULED: "Scheduled",
  IN_PROGRESS: "Live",
  COMPLETED: "Final",
};

export function MatchList({ matches, targetPoints, editable, onChanged }: Props) {
  const [scoring, setScoring] = useState<{ match: Match; correct: boolean } | null>(null);
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

            {editable && (
              <div className="mt-3 flex gap-2">
                {m.status === "SCHEDULED" && (
                  <>
                    <Button variant="secondary" className="flex-1" onClick={() => start(m)}>
                      Start
                    </Button>
                    <Button className="flex-1" onClick={() => setScoring({ match: m, correct: false })}>
                      Enter result
                    </Button>
                  </>
                )}
                {m.status === "IN_PROGRESS" && (
                  <Button className="flex-1" onClick={() => setScoring({ match: m, correct: false })}>
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
    </div>
  );
}
