import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "../lib/api";
import type { AdminPlayer } from "../lib/types";
import { Avatar } from "./Avatar";
import { Input } from "./ui";

interface Props {
  assignedIds: Set<string>;
  onPick: (playerId: string, player?: AdminPlayer) => void;
  onClose: () => void;
}

/** Mobile bottom-sheet to search approved players and add one to a team. */
export function PlayerPicker({ assignedIds, onPick, onClose }: Props) {
  const [q, setQ] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["approved-players"],
    queryFn: () => api<AdminPlayer[]>("/admin/players?approval_status=APPROVED"),
  });

  const candidates = useMemo(() => {
    const term = q.trim().toLowerCase();
    return (data ?? [])
      .filter((p) => !assignedIds.has(p.player_id))
      .filter((p) => !term || p.display_name.toLowerCase().includes(term));
  }, [data, q, assignedIds]);

  return (
    <div className="fixed inset-0 z-20 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="max-h-[80vh] rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Add a player</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">
            Close
          </button>
        </div>
        <Input placeholder="Search approved players…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="mt-3 max-h-[55vh] space-y-1 overflow-y-auto">
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : candidates.length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-500">No available approved players.</p>
          ) : (
            candidates.map((p) => (
              <button
                key={p.player_id}
                onClick={() => onPick(p.player_id, p)}
                className="flex w-full items-center gap-3 rounded-lg p-2 text-left active:bg-slate-100"
              >
                <Avatar name={p.display_name} size={40} />
                <span className="font-medium">{p.display_name}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
