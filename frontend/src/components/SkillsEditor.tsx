import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError, api } from "../lib/api";
import type { PlayerSkills } from "../lib/types";
import { Button } from "./ui";

interface Props {
  playerId: string;
  playerName: string;
  onClose: () => void;
  onSaved: () => void;
}

export function SkillsEditor({ playerId, playerName, onClose, onSaved }: Props) {
  const { data } = useQuery({
    queryKey: ["skills", playerId],
    queryFn: () => api<PlayerSkills>(`/players/${playerId}/skills`),
  });
  const [values, setValues] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setValues(Object.fromEntries(data.skills.map((s) => [s.key, s.value ?? 50])));
    }
  }, [data]);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await api(`/admin/players/${playerId}/skills`, {
        method: "PATCH",
        body: { ratings: values },
      });
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to save");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex flex-col justify-end bg-black/40" onClick={onClose}>
      <div
        className="max-h-[85vh] overflow-y-auto rounded-t-2xl bg-white p-4"
        style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1rem)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Skills · {playerName}</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-slate-500">
            Cancel
          </button>
        </div>

        <div className="space-y-4">
          {(data?.skills ?? []).map((s) => (
            <div key={s.key}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <label htmlFor={`skill-${s.key}`} className="font-medium text-slate-700">
                  {s.label}
                </label>
                <span className="w-10 text-right tabular-nums font-semibold">{values[s.key] ?? 50}</span>
              </div>
              <input
                id={`skill-${s.key}`}
                type="range"
                min={0}
                max={100}
                value={values[s.key] ?? 50}
                onChange={(e) => setValues((v) => ({ ...v, [s.key]: Number(e.target.value) }))}
                className="h-2 w-full cursor-pointer"
                aria-label={`${s.label} rating`}
              />
            </div>
          ))}
        </div>

        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        <Button className="mt-4 w-full" disabled={busy} onClick={save}>
          {busy ? "Saving…" : "Save skills"}
        </Button>
      </div>
    </div>
  );
}
