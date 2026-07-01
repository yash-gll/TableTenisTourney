import type { PlayerBreakdown, SkillCount } from "../lib/types";

function nonzero(items: SkillCount[]) {
  return items.filter((i) => i.count > 0);
}

function BarRow({ label, count, total, tone }: { label: string; count: number; total: number; tone: string }) {
  const pct = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-24 shrink-0 truncate text-slate-600">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-[4.5rem] shrink-0 whitespace-nowrap text-right text-xs tabular-nums text-slate-500">
        {count} · {pct}%
      </span>
    </div>
  );
}

function Group({
  title,
  dot,
  items,
  total,
  tone,
}: {
  title: string;
  dot: string;
  items: SkillCount[];
  total: number;
  tone: string;
}) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
        <span className={`inline-block h-2 w-2 rounded-full ${dot}`} />
        {title}
      </div>
      {items.map((i) => (
        <BarRow key={i.key} label={i.label} count={i.count} total={total} tone={tone} />
      ))}
    </div>
  );
}

export function ShotBreakdown({ breakdown, compact = false }: { breakdown: PlayerBreakdown; compact?: boolean }) {
  const b = breakdown;
  if (b.total_points === 0) {
    return <p className="text-sm text-slate-500">No rallies logged yet.</p>;
  }
  const winPct = Math.round((b.wins / b.total_points) * 100);
  const forcedPct = b.faults ? Math.round((b.forced_faults / b.faults) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* headline: win% + won/lost split bar */}
      <div>
        <div className="mb-1 flex items-baseline justify-between">
          <span className="text-2xl font-bold tabular-nums text-slate-800">{winPct}%</span>
          <span className="text-xs text-slate-500">
            <span className="font-semibold text-emerald-600">{b.wins} won</span> ·{" "}
            <span className="font-semibold text-rose-500">{b.faults} lost</span> · {b.total_points} decided
          </span>
        </div>
        <div className="flex h-2.5 overflow-hidden rounded-full bg-slate-100">
          <div className="bg-emerald-400" style={{ width: `${winPct}%` }} />
          <div className="bg-rose-400" style={{ width: `${100 - winPct}%` }} />
        </div>
      </div>

      <Group title="Winning shots" dot="bg-emerald-400" items={nonzero(b.win_by_skill)} total={b.wins} tone="bg-emerald-400" />
      <Group title="Mistakes" dot="bg-rose-400" items={nonzero(b.faults_by_type)} total={b.faults} tone="bg-rose-400" />

      {(b.faults > 0 || b.points_forced > 0) && (
        <div className="flex flex-wrap gap-2 text-xs">
          {b.faults > 0 && (
            <span className="rounded-full bg-rose-50 px-2.5 py-1 font-medium text-rose-600">
              {forcedPct}% of losses forced
            </span>
          )}
          {b.points_forced > 0 && (
            <span className="rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-600">
              forced {b.points_forced} opponent {b.points_forced === 1 ? "error" : "errors"}
            </span>
          )}
        </div>
      )}

      {!compact && (
        <p className="text-xs text-slate-400">
          Rallies this player won (own winners + errors they forced) or lost (own faults).
        </p>
      )}
    </div>
  );
}
