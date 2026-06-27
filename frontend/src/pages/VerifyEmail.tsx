import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { AuthShell } from "../components/AuthShell";
import { ApiError, api } from "../lib/api";

export function VerifyEmail() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("No verification token provided.");
      return;
    }
    api("/auth/verify-email", { method: "POST", body: { token }, auth: false })
      .then(() => {
        setState("ok");
        setMessage("Your email is verified. You can now sign in (pending admin approval).");
      })
      .catch((e) => {
        setState("error");
        setMessage(e instanceof ApiError ? e.message : "Verification failed.");
      });
  }, [token]);

  return (
    <AuthShell
      title={state === "ok" ? "Email verified" : state === "error" ? "Verification failed" : "Verifying…"}
      footer={<Link className="text-indigo-600 hover:underline" to="/login">Go to login</Link>}
    >
      <p className="text-sm text-slate-600">{message || "Please wait…"}</p>
    </AuthShell>
  );
}
