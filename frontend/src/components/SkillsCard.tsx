import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { PlayerSkills } from "../lib/types";
import { Card } from "./ui";

const CX = 160;
const CY = 120;
const R = 76;
const RL = 98; // label radius

function pointAt(i: number, n: number, val: number): [number, number] {
  const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
  const r = (R * val) / 100;
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
}
function toPoly(pts: [number, number][]): string {
  return pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
}

export function SkillsCard({ playerId }: { playerId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["skills", playerId],
    queryFn: () => api<PlayerSkills>(`/players/${playerId}/skills`),
  });
  if (isLoading || !data) return null;

  const skills = data.skills;
  const n = skills.length;
  const rings = [25, 50, 75, 100];

  return (
    <Card>
      <div className="flex justify-center">
        <svg viewBox="0 0 320 250" className="w-full max-w-[340px]">
          {rings.map((ring) => (
            <polygon
              key={ring}
              points={toPoly(skills.map((_, i) => pointAt(i, n, ring)))}
              fill={ring === 100 ? "rgb(248 250 252)" : "none"}
              stroke="rgb(226 232 240)"
              strokeWidth={1}
            />
          ))}
          {skills.map((_, i) => {
            const [x, y] = pointAt(i, n, 100);
            return (
              <line key={i} x1={CX} y1={CY} x2={x} y2={y} stroke="rgb(226 232 240)" strokeWidth={1} />
            );
          })}

          <polygon
            points={toPoly(skills.map((s, i) => pointAt(i, n, s.value ?? 0)))}
            fill="rgb(99 102 241 / 0.28)"
            stroke="rgb(79 70 229)"
            strokeWidth={2}
            strokeLinejoin="round"
          />
          {skills.map((s, i) => {
            const [x, y] = pointAt(i, n, s.value ?? 0);
            return <circle key={i} cx={x} cy={y} r={3.2} fill="rgb(79 70 229)" />;
          })}

          {skills.map((s, i) => {
            const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
            const lx = CX + RL * Math.cos(a);
            const ly = CY + RL * Math.sin(a);
            const cos = Math.cos(a);
            const anchor = Math.abs(cos) < 0.2 ? "middle" : cos > 0 ? "start" : "end";
            return (
              <text key={i} x={lx} y={ly} textAnchor={anchor} dominantBaseline="middle">
                <tspan x={lx} fontSize={9} fontWeight={600} fill="rgb(100 116 139)">
                  {s.label}
                </tspan>
                <tspan x={lx} dy={12} fontSize={11} fontWeight={700} fill="rgb(30 41 59)">
                  {s.value ?? "—"}
                </tspan>
              </text>
            );
          })}
        </svg>
      </div>
    </Card>
  );
}
