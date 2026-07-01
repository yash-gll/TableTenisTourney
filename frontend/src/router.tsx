import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./lib/auth";
import { AdminPendingPlayers } from "./pages/AdminPendingPlayers";
import { Dashboard } from "./pages/Dashboard";
import { ForgotPassword } from "./pages/ForgotPassword";
import { HistoryDetailPage, HistoryList } from "./pages/History";
import { Landing } from "./pages/Landing";
import { LivePage } from "./pages/Live";
import { ComparePage } from "./pages/Compare";
import { CompareTeamsPage } from "./pages/CompareTeams";
import { ExhibitionDetail } from "./pages/ExhibitionDetail";
import { Exhibitions } from "./pages/Exhibitions";
import { Login } from "./pages/Login";
import { PlayersDirectory, PublicProfilePage } from "./pages/Players";
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
        path="/players"
        element={
          <RequireAuth>
            <PlayersDirectory />
          </RequireAuth>
        }
      />
      <Route
        path="/players/compare"
        element={
          <RequireAuth>
            <ComparePage />
          </RequireAuth>
        }
      />
      <Route
        path="/players/compare-teams"
        element={
          <RequireAuth>
            <CompareTeamsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/players/:id"
        element={
          <RequireAuth>
            <PublicProfilePage />
          </RequireAuth>
        }
      />
      <Route
        path="/live"
        element={
          <RequireAuth>
            <LivePage />
          </RequireAuth>
        }
      />
      <Route
        path="/tournaments"
        element={
          <RequireAuth>
            <TournamentList />
          </RequireAuth>
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
        path="/exhibitions"
        element={
          <RequireAdmin>
            <Exhibitions />
          </RequireAdmin>
        }
      />
      <Route
        path="/exhibitions/:matchId"
        element={
          <RequireAdmin>
            <ExhibitionDetail />
          </RequireAdmin>
        }
      />
      <Route
        path="/tournaments/:id"
        element={
          <RequireAuth>
            <TournamentDetail />
          </RequireAuth>
        }
      />
      <Route
        path="/history"
        element={
          <RequireAuth>
            <HistoryList />
          </RequireAuth>
        }
      />
      <Route
        path="/history/:id"
        element={
          <RequireAuth>
            <HistoryDetailPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
