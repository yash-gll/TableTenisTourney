import type { Bracket, Match } from "../lib/types";
import { Card } from "./ui";

const STAGE_LABEL: Record<string, string> = {
  QF1: "QF1 · Rank 1 vs Rank 2",
  QF2: "QF2 · Rank 3 vs Rank 4",
  QF3: "QF3 · Winner QF2 vs Loser QF1",
  FINAL: "Final · Winner QF1 vs Winner QF3",
};

const MEDAL = ["", "🥇", "🥈", "🥉", "4th"];

function BracketMatch({ m }: { m: Match }) {
  const side = (name: string | null, id: string | null, score: number | null) => (
    <div
      className={`flex items-center justify-between rounded-md px-2 py-1 ${
        m.winner_team_id && m.winner_team_id === id ? "bg-emerald-50 font-semibold" : ""
      }`}
    >
      <span className="truncate">{name ?? "TBD"}</span>
      {score != null && <span className="tabular-nums">{score}</span>}
    </div>
  );
  return (
    <Card className="space-y-1">
      <div className="text-xs font-medium uppercase text-slate-400">{STAGE_LABEL[m.stage]}</div>
      {side(m.team_a_name, m.team_a_id, m.team_a_score)}
      {side(m.team_b_name, m.team_b_id, m.team_b_score)}
    </Card>
  );
}

export function BracketView({ data }: { data: Bracket }) {
  const order = ["QF1", "QF2", "QF3", "FINAL"];
  const matches = [...data.matches].sort(
    (x, y) => order.indexOf(x.stage) - order.indexOf(y.stage),
  );

  return (
    <div className="space-y-3">
      {matches.map((m) => (
        <BracketMatch key={m.id} m={m} />
      ))}

      {data.placements.length > 0 && (
        <Card>
          <h3 className="mb-2 text-sm font-semibold">Placements</h3>
          <ul className="space-y-1 text-sm">
            {data.placements.map((p) => (
              <li key={p.team_id} className="flex items-center gap-2">
                <span>{MEDAL[p.place] ?? `${p.place}th`}</span>
                <span className={p.place === 1 ? "font-semibold" : ""}>{p.team_name}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
