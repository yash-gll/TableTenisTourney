import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { AuthShell } from "../components/AuthShell";
import { Button, FormError, Input } from "../components/ui";
import { ApiError, api } from "../lib/api";

const schema = z.object({
  display_name: z.string().min(1, "Display name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export function Register() {
  const [done, setDone] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await api("/auth/register", { method: "POST", body: values, auth: false });
      setDone(true);
    } catch (e) {
      setServerError(e instanceof ApiError ? e.message : "Registration failed");
    }
  };

  if (done) {
    return (
      <AuthShell
        title="Check your verification link"
        subtitle="Your account was created. In this dev build the verification link is printed to the backend logs. After verifying, an administrator must approve you before you can join tournaments."
        footer={<Link className="text-indigo-600 hover:underline" to="/login">Go to login</Link>}
      >
        <p className="text-sm text-slate-600">
          Once verified and approved, sign in to access your dashboard.
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Create your account"
      footer={
        <span>
          Already have an account?{" "}
          <Link className="text-indigo-600 hover:underline" to="/login">
            Sign in
          </Link>
        </span>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <div>
          <Input placeholder="Display name" {...register("display_name")} />
          <FormError message={errors.display_name?.message} />
        </div>
        <div>
          <Input type="email" placeholder="Email" {...register("email")} />
          <FormError message={errors.email?.message} />
        </div>
        <div>
          <Input type="password" placeholder="Password" {...register("password")} />
          <FormError message={errors.password?.message} />
        </div>
        <FormError message={serverError ?? undefined} />
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Register"}
        </Button>
      </form>
    </AuthShell>
  );
}
