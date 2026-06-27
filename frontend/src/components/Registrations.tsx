import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "../lib/api";
import type { MyRegistration, RegistrationItem } from "../lib/types";
import { Avatar } from "./Avatar";
import { Button, Card } from "./ui";

const STATUS_STYLE: Record<string, string> = {
  REQUESTED: "bg-sky-100 text-sky-700",
  ACCEPTED: "bg-emerald-100 text-emerald-700",
  WAITLISTED: "bg-amber-100 text-amber-700",
  DECLINED: "bg-rose-100 text-rose-700",
  WITHDRAWN: "bg-slate-100 text-slate-600",
};

/** Player-facing "request to join" card for an open tournament. */
export function PlayerRegistration({ tournamentId }: { tournamentId: string }) {
  const queryClient = useQueryClient();
  const key = ["my-registration", tournamentId];
  const { data } = useQuery({
    queryKey: key,
    queryFn: () => api<MyRegistration>(`/tournaments/${tournamentId}/registrations/me`),
  });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: key });

  const join = useMutation({
    mutationFn: () => api(`/tournaments/${tournamentId}/registrations`, { method: "POST", body: {} }),
    onSuccess: invalidate,
  });
  const withdraw = useMutation({
    mutationFn: () => api(`/tournaments/${tournamentId}/registrations/me`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  const status = data?.status ?? null;
  const active = status === "REQUESTED" || status === "ACCEPTED" || status === "WAITLISTED";

  return (
    <Card className="border-sky-200 bg-sky-50">
      <h2 className="font-semibold text-sky-900">Registration is open</h2>
      {active ? (
        <div className="mt-2 flex items-center justify-between">
          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLE[status!]}`}>
            {status === "ACCEPTED" ? "You're in 🎉" : status === "WAITLISTED" ? "Waitlisted" : "Requested"}
          </span>
          {status !== "ACCEPTED" && (
            <button
              onClick={() => withdraw.mutate()}
              className="text-sm font-medium text-rose-600 active:opacity-70"
            >
              Withdraw
            </button>
          )}
        </div>
      ) : (
        <>
          <p className="mt-1 text-sm text-sky-800">
            Request to join — the organizer will review and form teams.
          </p>
          <Button className="mt-3 w-full" disabled={join.isPending} onClick={() => join.mutate()}>
            {join.isPending ? "Requesting…" : "Request to join"}
          </Button>
          {join.error instanceof ApiError && (
            <p className="mt-2 text-sm text-rose-600">{join.error.message}</p>
          )}
        </>
      )}
    </Card>
  );
}

/** Admin panel listing signups with accept/decline. */
export function AdminRegistrations({ tournamentId }: { tournamentId: string }) {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["registrations", tournamentId],
    queryFn: () => api<RegistrationItem[]>(`/tournaments/${tournamentId}/registrations`),
  });
  const act = useMutation({
    mutationFn: ({ pid, action }: { pid: string; action: string }) =>
      api(`/tournaments/${tournamentId}/registrations/${pid}/${action}`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["registrations", tournamentId] }),
  });

  if (!data || data.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
        Sign-ups ({data.length})
      </h3>
      {data.map((r) => (
        <Card key={r.player_id} className="flex items-center gap-3">
          <Avatar name={r.display_name} size={40} />
          <div className="min-w-0 flex-1">
            <div className="font-medium">{r.display_name}</div>
            {r.note && <div className="truncate text-xs text-slate-500">{r.note}</div>}
          </div>
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[r.status]}`}>
            {r.status}
          </span>
          {(r.status === "REQUESTED" || r.status === "WAITLISTED") && (
            <div className="flex shrink-0 gap-1">
              <button
                onClick={() => act.mutate({ pid: r.player_id, action: "accept" })}
                className="rounded-md bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white active:bg-emerald-700"
              >
                Accept
              </button>
              <button
                onClick={() => act.mutate({ pid: r.player_id, action: "decline" })}
                className="rounded-md px-2.5 py-1 text-xs font-medium text-rose-600 active:bg-rose-50"
              >
                Decline
              </button>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}
