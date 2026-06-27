import type { Leaderboard } from "../lib/types";
import { Card } from "./ui";

export function LeaderboardTable({
  data,
  explanation,
}: {
  data: Leaderboard;
  explanation: string[];
}) {
  return (
    <div className="space-y-3">
      {!data.group_complete && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">
          Provisional — standings update as group matches complete.
        </p>
      )}
      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
              <th className="px-3 py-2">#</th>
              <th className="px-2 py-2">Team</th>
              <th className="px-2 py-2 text-right">W</th>
              <th className="px-2 py-2 text-right">L</th>
              <th className="px-2 py-2 text-right">Pts</th>
              <th className="px-2 py-2 text-right">Diff</th>
            </tr>
          </thead>
          <tbody>
            {data.standings.map((s) => {
              const qualified = s.qualification_status === "QUALIFIED";
              return (
                <tr
                  key={s.team_id}
                  className={`border-b border-slate-100 ${qualified ? "bg-emerald-50" : ""}`}
                >
                  <td className="px-3 py-2 font-medium">{s.rank}</td>
                  <td className="px-2 py-2">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium">{s.team_name}</span>
                      {qualified && <span title="Qualified">✓</span>}
                      {s.tie_status === "UNRESOLVED" && (
                        <span className="text-xs text-rose-600" title="Unresolved tie">
                          ⚠
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400">
                      {s.points_for}–{s.points_against}
                    </div>
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums">{s.wins}</td>
                  <td className="px-2 py-2 text-right tabular-nums">{s.losses}</td>
                  <td className="px-2 py-2 text-right tabular-nums">{s.table_points}</td>
                  <td className="px-2 py-2 text-right tabular-nums">
                    {s.point_difference >= 0 ? "+" : ""}
                    {s.point_difference}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {explanation.length > 0 && (
        <Card>
          <h3 className="mb-1 text-sm font-semibold">Tie-breaks applied</h3>
          <ul className="list-disc space-y-1 pl-5 text-xs text-slate-600">
            {explanation.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
