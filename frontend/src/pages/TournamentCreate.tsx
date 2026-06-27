import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { AppShell } from "../components/AppShell";
import { Button, Card, FormError, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";
import type { Tournament } from "../lib/types";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  location: z.string().optional(),
  description: z.string().optional(),
  visibility: z.enum(["PUBLIC", "PRIVATE", "UNLISTED"]),
  target_points: z.coerce.number().int().min(1).max(99),
  win_by_two: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

export function TournamentCreate() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { visibility: "PUBLIC", target_points: 11, win_by_two: false },
  });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      const t = await api<Tournament>("/tournaments", {
        method: "POST",
        body: {
          name: values.name,
          location: values.location || null,
          description: values.description || null,
          visibility: values.visibility,
          scoring: {
            target_points: values.target_points,
            win_by_two: values.win_by_two,
            win_table_points: 2,
            loss_table_points: 0,
          },
        },
      });
      navigate(`/tournaments/${t.id}`);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Failed to create tournament");
    }
  };

  return (
    <AppShell title="New tournament">
      <Card>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <label className="text-sm text-slate-600">Name</label>
            <Input placeholder="e.g. Summer Doubles Cup" {...register("name")} />
            <FormError message={errors.name?.message} />
          </div>
          <div>
            <label className="text-sm text-slate-600">Location</label>
            <Input placeholder="Optional" {...register("location")} />
          </div>
          <div>
            <label className="text-sm text-slate-600">Description</label>
            <textarea
              className="min-h-11 w-full rounded-lg border border-slate-300 px-3.5 py-3 text-base focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              rows={2}
              placeholder="Optional"
              {...register("description")}
            />
          </div>
          <div>
            <label className="text-sm text-slate-600">Visibility</label>
            <select
              className="min-h-11 w-full rounded-lg border border-slate-300 px-3 py-3 text-base"
              {...register("visibility")}
            >
              <option value="PUBLIC">Public</option>
              <option value="UNLISTED">Unlisted</option>
              <option value="PRIVATE">Private</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-slate-600">Points to win</label>
              <Input type="number" {...register("target_points")} />
            </div>
            <label className="flex items-center gap-2 pt-7 text-sm text-slate-700">
              <input type="checkbox" className="h-5 w-5" {...register("win_by_two")} />
              Win by two
            </label>
          </div>
          <FormError message={serverError ?? undefined} />
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating…" : "Create tournament"}
          </Button>
        </form>
      </Card>
    </AppShell>
  );
}
