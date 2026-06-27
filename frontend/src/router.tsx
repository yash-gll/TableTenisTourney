import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./lib/auth";
import { AdminPendingPlayers } from "./pages/AdminPendingPlayers";
import { Dashboard } from "./pages/Dashboard";
import { ForgotPassword } from "./pages/ForgotPassword";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { ResetPassword } from "./pages/ResetPassword";
import { TournamentCreate } from "./pages/TournamentCreate";
import { TournamentDetail } from "./pages/TournamentDetail";
import { TournamentList } from "./pages/TournamentList";
import { VerifyEmail } from "./pages/VerifyEmail";

function FullScreenMessage({ children }: { children: ReactNode }) {
  return <div className="flex min-h-dvh items-center justify-center text-slate-500">{children}</div>;
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenMessage>Loading…</FullScreenMessage>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenMessage>Loading…</FullScreenMessage>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "PLAYER") return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAdmin>
            <AdminPendingPlayers />
          </RequireAdmin>
        }
      />
      <Route
        path="/tournaments"
        element={
          <RequireAdmin>
            <TournamentList />
          </RequireAdmin>
        }
      />
      <Route
        path="/tournaments/new"
        element={
          <RequireAdmin>
            <TournamentCreate />
          </RequireAdmin>
        }
      />
      <Route
        path="/tournaments/:id"
        element={
          <RequireAdmin>
            <TournamentDetail />
          </RequireAdmin>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
