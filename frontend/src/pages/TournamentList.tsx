import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { Button, Card } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Tournament } from "../lib/types";

const STATUS_STYLE: Record<string, string> = {
  DRAFT: "bg-slate-100 text-slate-600",
  REGISTRATION_OPEN: "bg-sky-100 text-sky-700",
  REGISTRATION_CLOSED: "bg-amber-100 text-amber-700",
  CANCELLED: "bg-rose-100 text-rose-700",
};

export function TournamentList() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const { data, isLoading } = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => api<Tournament[]>("/tournaments"),
  });

  return (
    <AppShell title="Tournaments">
      <div className="space-y-4">
        {isAdmin && (
          <div className="flex gap-2">
            <Button className="flex-1" onClick={() => navigate("/tournaments/new")}>
              + New tournament
            </Button>
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => navigate("/exhibitions")}
            >
              Exhibition matches
            </Button>
          </div>
        )}

        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !data || data.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-500">
              {isAdmin
                ? "No tournaments yet. Create your first one."
                : "You're not in any active tournaments yet. They'll appear here once an admin starts one you're in."}
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {data.map((t) => (
              <Link key={t.id} to={`/tournaments/${t.id}`} className="block">
                <Card className="active:bg-slate-50">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{t.name}</div>
                      <div className="text-sm text-slate-500">
                        {t.team_count} {t.team_count === 1 ? "team" : "teams"} ·{" "}
                        {t.visibility.toLowerCase()}
                      </div>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                        STATUS_STYLE[t.status] ?? "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {t.status.replace(/_/g, " ")}
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
