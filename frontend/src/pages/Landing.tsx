import { Link } from "react-router-dom";

import { Button } from "../components/ui";
import { useAuth } from "../lib/auth";

export function Landing() {
  const { user } = useAuth();
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 p-4 text-center">
      <h1 className="text-3xl font-bold text-indigo-700">🏓 Table Tennis Tournaments</h1>
      <p className="max-w-md text-slate-600">
        Run team-based table tennis tournaments — registration, approval, round-robin group stages,
        brackets, and Elo ratings.
      </p>
      <div className="flex gap-3">
        {user ? (
          <Link to="/dashboard">
            <Button>Go to dashboard</Button>
          </Link>
        ) : (
          <>
            <Link to="/login">
              <Button>Sign in</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary">Register</Button>
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
