import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { RatingEvent } from "../lib/types";
import { Card } from "./ui";

const W = 300;
const H = 64;
const PAD = 6;

export function RatingSparkline({ playerId }: { playerId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["rating-events", playerId],
    queryFn: () => api<RatingEvent[]>(`/players/${playerId}/rating-events`),
  });

  if (isLoading || !data) return null;

  // Build the rating series over time (starting value + each rating_after).
  const series = data.length ? [data[0].rating_before, ...data.map((e) => e.rating_after)] : [];

  if (series.length < 2) {
    return (
      <Card>
        <p className="text-sm text-slate-500">Not enough match history for a trend yet.</p>
      </Card>
    );
  }

  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const stepX = (W - PAD * 2) / (series.length - 1);
  const points = series.map((v, i) => {
    const x = PAD + i * stepX;
    const y = PAD + (H - PAD * 2) * (1 - (v - min) / span);
    return [x, y] as const;
  });
  const path = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const last = points[points.length - 1];
  const up = series[series.length - 1] >= series[0];

  return (
    <Card>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-sm text-slate-500">Rating trend</span>
        <span className="text-sm font-semibold tabular-nums">
          {min} – {max}
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" preserveAspectRatio="none" role="img"
        aria-label="Rating over time">
        <polyline
          points={path}
          fill="none"
          stroke={up ? "#10b981" : "#f43f5e"}
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={last[0]} cy={last[1]} r="3" fill={up ? "#10b981" : "#f43f5e"} />
      </svg>
    </Card>
  );
}
