import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { Avatar } from "../components/Avatar";
import { Button, Card, Input, StatusBadge } from "../components/ui";
import { api } from "../lib/api";
import type { PlayerProfile } from "../lib/types";

function StatusBanner({ profile }: { profile: PlayerProfile }) {
  if (profile.approval_status === "PENDING") {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <h2 className="font-semibold text-amber-800">Awaiting approval</h2>
        <p className="mt-1 text-sm text-amber-700">
          Your account is verified and pending administrator approval. You'll be able to join
          tournaments once approved.
        </p>
      </Card>
    );
  }
  if (profile.approval_status === "REJECTED" || profile.approval_status === "SUSPENDED") {
    const label = profile.approval_status === "REJECTED" ? "Account rejected" : "Account suspended";
    return (
      <Card className="border-rose-200 bg-rose-50">
        <h2 className="font-semibold text-rose-800">{label}</h2>
        {profile.approval_reason && (
          <p className="mt-1 text-sm text-rose-700">Reason: {profile.approval_reason}</p>
        )}
      </Card>
    );
  }
  return (
    <Card className="border-emerald-200 bg-emerald-50">
      <h2 className="font-semibold text-emerald-800">Approved</h2>
      <p className="mt-1 text-sm text-emerald-700">
        You're approved. Tournament participation arrives in a later phase.
      </p>
    </Card>
  );
}

export function Dashboard() {
  const queryClient = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ["me-profile"],
    queryFn: () => api<PlayerProfile>("/players/me"),
  });

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name);
      setBio(profile.bio ?? "");
    }
  }, [profile]);

  const mutation = useMutation({
    mutationFn: () =>
      api<PlayerProfile>("/players/me", {
        method: "PATCH",
        body: { display_name: displayName, bio },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me-profile"] }),
  });

  return (
    <AppShell title="Profile">
      <div className="space-y-6">
        {isLoading || !profile ? (
          <p className="text-slate-500">Loading…</p>
        ) : (
          <>
            <div className="flex items-center gap-4">
              <Avatar name={profile.display_name} size={64} />
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold">{profile.display_name}</h1>
                  <StatusBadge status={profile.approval_status} />
                </div>
                <p className="text-sm text-slate-500">{profile.email}</p>
              </div>
            </div>

            <StatusBanner profile={profile} />

            <Card>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-slate-500">Current rating</div>
                  <div className="text-lg font-semibold">{profile.current_rating}</div>
                </div>
                <div>
                  <div className="text-slate-500">Highest rating</div>
                  <div className="text-lg font-semibold">{profile.highest_rating}</div>
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="font-semibold">Edit profile</h2>
              <div className="mt-4 space-y-3">
                <div>
                  <label className="text-sm text-slate-600">Display name</label>
                  <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
                </div>
                <div>
                  <label className="text-sm text-slate-600">Bio</label>
                  <textarea
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    rows={3}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                  />
                </div>
                <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
                  {mutation.isPending ? "Saving…" : "Save changes"}
                </Button>
                {mutation.isSuccess && <span className="ml-2 text-sm text-emerald-600">Saved.</span>}
              </div>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
