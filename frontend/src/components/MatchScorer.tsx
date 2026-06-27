import { useState } from "react";

import type { Match } from "../lib/types";
import { Button } from "./ui";

interface Props {
  match: Match;
  targetPoints: number;
  requireReason: boolean;
  onSubmit: (a: number, b: number, reason: string) => void;
  onClose: () => void;
  busy?: boolean;
  error?: string | null;
}

function Stepper({
  label,
  value,
  onChange,
  max,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  max: number;
}) {
  return (
    <div className="flex-1 rounded-xl border border-slate-200 p-3 text-center">
      <div className="mb-2 truncate text-sm font-medium text-slate-700">{label}</div>
      <div className="text-4xl font-bold tabular-nums">{value}</div>
      <div className="mt-3 flex justify-center gap-2">
        <button
          onClick={() => onChange(Math.max(0, value - 1))}
          className="h-11 w-11 rounded-full bg-slate-200 text-2xl font-bold active:bg-slate-300"
        >
          −
        </button>
        <button
          onClick={() => onChange(Math.min(max, value + 1))}
          className="h-11 w-11 rounded-full bg-indigo-600 text-2xl font-bold text-white active:bg-indigo-700"
        >
          +
        </button>
      </div>
    </div>
  );
}

export function MatchScorer({
  match,
  targetPoints,
  requireReason,
  onSubmit,
  onClose,
  busy,
  error,
}: Props) {
  const [a, setA] = useState(match.team_a_score ?? 0);
  const [b, setB] = useState(match.team_b_score ?? 0);
  const [reason, setReason] = useState("");
  const max = Math.max(targetPoints + 20, 30);
  const canSubmit = a !== b && (!requireReason || reason.trim().length > 0);

  return (
    <div className="fixed inset-0 z-30 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">{requireReason ? "Correct result" : "Enter result"}</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">
            Cancel
          </button>
        </div>

        <div className="flex items-stretch gap-3">
          <Stepper label={match.team_a_name ?? "Team A"} value={a} onChange={setA} max={max} />
          <Stepper label={match.team_b_name ?? "Team B"} value={b} onChange={setB} max={max} />
        </div>

        {a === b && <p className="mt-2 text-center text-sm text-amber-600">Scores can't be tied.</p>}

        {requireReason && (
          <input
            className="mt-3 min-h-11 w-full rounded-lg border border-slate-300 px-3.5 py-3 text-base"
            placeholder="Reason for correction"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        )}

        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}

        <Button
          className="mt-4 w-full"
          disabled={!canSubmit || busy}
          onClick={() => onSubmit(a, b, reason)}
        >
          {busy ? "Saving…" : "Save result"}
        </Button>
      </div>
    </div>
  );
}
