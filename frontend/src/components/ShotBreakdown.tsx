import type { PlayerBreakdown, SkillCount } from "../lib/types";

function BarRow({ label, count, total, tone }: { label: string; count: number; total: number; tone: string }) {
  const pct = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-24 shrink-0 truncate text-slate-600">{label}</span>
      <div className="h-2 flex-1 rounded bg-slate-100">
        <div className={`h-2 rounded ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-16 shrink-0 text-right tabular-nums text-xs text-slate-500">
        {count} · {pct}%
      </span>
    </div>
  );
}

function nonzero(items: SkillCount[]) {
  return items.filter((i) => i.count > 0);
}

export function ShotBreakdown({ breakdown, compact = false }: { breakdown: PlayerBreakdown; compact?: boolean }) {
  const b = breakdown;
  if (b.total_points === 0) {
    return <p className="text-sm text-slate-500">No rallies logged yet.</p>;
  }
  const winPct = Math.round((b.wins / b.total_points) * 100);
  const forcedPct = b.faults ? Math.round((b.forced_faults / b.faults) * 100) : 0;
  const wins = nonzero(b.win_by_skill);
  const faults = nonzero(b.faults_by_type);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-emerald-600">{b.wins} won</span>
        <span className="text-slate-400">{winPct}% of {b.total_points}</span>
        <span className="font-medium text-rose-500">{b.faults} lost</span>
      </div>
      {!compact && (
        <p className="-mt-1 text-xs text-slate-400">
          Rallies this player won (own winners + errors they forced) or lost (own faults).
        </p>
      )}

      {wins.length > 0 && (
        <div className="space-y-1">
          {!compact && <div className="text-xs font-semibold uppercase text-slate-400">How points are won</div>}
          {wins.map((w) => (
            <BarRow key={w.key} label={w.label} count={w.count} total={b.wins} tone="bg-emerald-400" />
          ))}
        </div>
      )}

      {faults.length > 0 && (
        <div className="space-y-1">
          {!compact && <div className="text-xs font-semibold uppercase text-slate-400">How points are lost</div>}
          {faults.map((f) => (
            <BarRow key={f.key} label={f.label} count={f.count} total={b.faults} tone="bg-rose-400" />
          ))}
        </div>
      )}

      <div className="text-xs text-slate-500">
        {b.faults > 0 && <>{forcedPct}% of losses were forced · </>}
        forced {b.points_forced} opponent {b.points_forced === 1 ? "error" : "errors"}
      </div>
    </div>
  );
}
