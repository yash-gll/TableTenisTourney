import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { AuthShell } from "../components/AuthShell";
import { Button, FormError, Input } from "../components/ui";
import { api } from "../lib/api";

const schema = z.object({ email: z.string().email("Enter a valid email") });
type FormValues = z.infer<typeof schema>;

export function ForgotPassword() {
  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    await api("/auth/forgot-password", { method: "POST", body: values, auth: false });
    setDone(true);
  };

  return (
    <AuthShell
      title="Reset your password"
      subtitle="If the account exists, a reset link is generated (printed to the backend logs in this dev build)."
      footer={<Link className="text-indigo-600 hover:underline" to="/login">Back to login</Link>}
    >
      {done ? (
        <p className="text-sm text-slate-600">Check the backend logs for your reset link.</p>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <Input type="email" placeholder="Email" {...register("email")} />
            <FormError message={errors.email?.message} />
          </div>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
