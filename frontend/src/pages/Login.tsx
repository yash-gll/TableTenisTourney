import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { AuthShell } from "../components/AuthShell";
import { Button, FormError, Input } from "../components/ui";
import { ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      const me = await login(values.email, values.password);
      if (me.role === "ADMIN" || me.role === "SUPER_ADMIN") navigate("/admin");
      else navigate("/");
    } catch (e) {
      if (e instanceof ApiError && e.code === "EMAIL_NOT_VERIFIED") {
        setServerError("Your email is not verified yet. Check the verification link (backend logs).");
      } else {
        setServerError(e instanceof ApiError ? e.message : "Login failed");
      }
    }
  };

  return (
    <AuthShell
      title="Sign in"
      footer={
        <div className="space-y-1">
          <div>
            No account?{" "}
            <Link className="text-indigo-600 hover:underline" to="/register">
              Register
            </Link>
          </div>
          <div>
            <Link className="text-indigo-600 hover:underline" to="/forgot-password">
              Forgot password?
            </Link>
          </div>
        </div>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
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
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
