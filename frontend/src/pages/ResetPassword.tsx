import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { AuthShell } from "../components/AuthShell";
import { Button, FormError, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";

const schema = z.object({ password: z.string().min(8, "At least 8 characters") });
type FormValues = z.infer<typeof schema>;

export function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [done, setDone] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    if (!token) {
      setServerError("Missing reset token.");
      return;
    }
    try {
      await api("/auth/reset-password", {
        method: "POST",
        body: { token, password: values.password },
        auth: false,
      });
      setDone(true);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Reset failed");
    }
  };

  return (
    <AuthShell
      title="Choose a new password"
      footer={<Link className="text-indigo-600 hover:underline" to="/login">Back to login</Link>}
    >
      {done ? (
        <p className="text-sm text-slate-600">Password updated. You can now sign in.</p>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <Input type="password" placeholder="New password" {...register("password")} />
            <FormError message={errors.password?.message} />
          </div>
          <FormError message={serverError ?? undefined} />
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Update password"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
