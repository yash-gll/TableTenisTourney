import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Avatar } from "../components/Avatar";
import { TopBar } from "../components/TopBar";
import { Button, Card, StatusBadge } from "../components/ui";
import { api } from "../lib/api";
import type { AdminPlayer, ApprovalStatus } from "../lib/types";

const FILTERS: ApprovalStatus[] = ["PENDING", "APPROVED", "REJECTED", "SUSPENDED"];

export function AdminPendingPlayers() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<ApprovalStatus>("PENDING");

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
    <div>
      <TopBar />
      <main className="mx-auto max-w-4xl space-y-4 p-4">
        <h1 className="text-xl font-semibold">Player management</h1>

        <div className="flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-md px-3 py-1.5 text-sm ${
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
              <Card key={p.player_id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar name={p.display_name} size={44} />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{p.display_name}</span>
                      <StatusBadge status={p.approval_status} />
                      {!p.email_verified && (
                        <span className="text-xs text-amber-600">unverified</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500">{p.email}</div>
                    {p.approval_reason && (
                      <div className="text-xs text-slate-400">Reason: {p.approval_reason}</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  {(p.approval_status === "PENDING" || p.approval_status === "REJECTED") && (
                    <Button onClick={() => act.mutate({ id: p.player_id, action: "approve" })}>
                      Approve
                    </Button>
                  )}
                  {p.approval_status === "PENDING" && (
                    <Button variant="danger" onClick={() => doReject(p.player_id)}>
                      Reject
                    </Button>
                  )}
                  {p.approval_status === "APPROVED" && (
                    <Button variant="danger" onClick={() => doSuspend(p.player_id)}>
                      Suspend
                    </Button>
                  )}
                  {p.approval_status === "SUSPENDED" && (
                    <Button onClick={() => act.mutate({ id: p.player_id, action: "restore" })}>
                      Restore
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
