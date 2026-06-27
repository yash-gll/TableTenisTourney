import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { SkillsEditor } from "../components/SkillsEditor";
import { Button, Card, StatusBadge } from "../components/ui";
import { api } from "../lib/api";
import type { AdminPlayer, ApprovalStatus } from "../lib/types";

const FILTERS: ApprovalStatus[] = ["PENDING", "APPROVED", "REJECTED", "SUSPENDED"];

export function AdminPendingPlayers() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<ApprovalStatus>("PENDING");
  const [editingSkills, setEditingSkills] = useState<AdminPlayer | null>(null);

  const { data: players, isLoading } = useQuery({
    queryKey: ["admin-players", filter],
    queryFn: () => api<AdminPlayer[]>(`/admin/players?approval_status=${filter}`),
  });

  const act = useMutation({
    mutationFn: ({ id, action, reason }: { id: string; action: string; reason?: string }) =>
      api(`/admin/players/${id}/${action}`, {
        method: "POST",
        body: reason !== undefined ? { reason } : undefined,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-players"] }),
  });

  const doReject = (id: string) => {
    const reason = window.prompt("Reason for rejection?");
    if (reason) act.mutate({ id, action: "reject", reason });
  };
  const doSuspend = (id: string) => {
    const reason = window.prompt("Reason for suspension?");
    if (reason) act.mutate({ id, action: "suspend", reason });
  };

  return (
    <AppShell title="Players">
      <div className="space-y-4">
        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium ${
                filter === f ? "bg-indigo-600 text-white" : "bg-white text-slate-600 border border-slate-200"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !players || players.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">No players with status {filter}.</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {players.map((p) => (
              <Card key={p.player_id} className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <Avatar name={p.display_name} size={44} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{p.display_name}</span>
                      <StatusBadge status={p.approval_status} />
                      {!p.email_verified && (
                        <span className="text-xs text-amber-600">unverified</span>
                      )}
                    </div>
                    <div className="truncate text-sm text-slate-500">{p.email}</div>
                    {p.approval_reason && (
                      <div className="text-xs text-slate-400">Reason: {p.approval_reason}</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  {(p.approval_status === "PENDING" || p.approval_status === "REJECTED") && (
                    <Button
                      className="flex-1"
                      onClick={() => act.mutate({ id: p.player_id, action: "approve" })}
                    >
                      Approve
                    </Button>
                  )}
                  {p.approval_status === "PENDING" && (
                    <Button variant="danger" className="flex-1" onClick={() => doReject(p.player_id)}>
                      Reject
                    </Button>
                  )}
                  {p.approval_status === "APPROVED" && (
                    <Button variant="danger" className="flex-1" onClick={() => doSuspend(p.player_id)}>
                      Suspend
                    </Button>
                  )}
                  {p.approval_status === "SUSPENDED" && (
                    <Button
                      className="flex-1"
                      onClick={() => act.mutate({ id: p.player_id, action: "restore" })}
                    >
                      Restore
                    </Button>
                  )}
                  <Button variant="secondary" onClick={() => setEditingSkills(p)}>
                    Skills
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {editingSkills && (
        <SkillsEditor
          playerId={editingSkills.player_id}
          playerName={editingSkills.display_name}
          onClose={() => setEditingSkills(null)}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ["skills", editingSkills.player_id] });
            setEditingSkills(null);
          }}
        />
      )}
    </AppShell>
  );
}
