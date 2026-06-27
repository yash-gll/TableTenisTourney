import type { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { Avatar } from "./Avatar";

function ProfileIcon({ active }: { active: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={active ? 2.4 : 1.8}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-3.3 3.6-6 8-6s8 2.7 8 6" strokeLinecap="round" />
    </svg>
  );
}

function PlayersIcon({ active }: { active: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={active ? 2.4 : 1.8}>
      <circle cx="9" cy="8" r="3.2" />
      <circle cx="17" cy="9" r="2.6" />
      <path d="M3 19c0-2.8 2.7-5 6-5s6 2.2 6 5" strokeLinecap="round" />
      <path d="M15.5 14c2.5 0 5 1.6 5 4" strokeLinecap="round" />
    </svg>
  );
}

function TrophyIcon({ active }: { active: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={active ? 2.4 : 1.8}>
      <path d="M7 4h10v4a5 5 0 0 1-10 0V4z" strokeLinejoin="round" />
      <path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3" strokeLinecap="round" />
      <path d="M12 13v4M9 20h6M10 20v-1.5h4V20" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

interface Tab {
  to: string;
  label: string;
  icon: (p: { active: boolean }) => ReactNode;
}

export function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const tabs: Tab[] = [{ to: "/dashboard", label: "Profile", icon: ProfileIcon }];
  if (isAdmin) {
    tabs.push({ to: "/tournaments", label: "Tournaments", icon: TrophyIcon });
    tabs.push({ to: "/admin", label: "Players", icon: PlayersIcon });
  }
  const showBottomNav = tabs.length > 1;

  // Highlight the Tournaments tab on nested tournament routes too.
  const isActive = (to: string) =>
    location.pathname === to || (to === "/tournaments" && location.pathname.startsWith("/tournaments"));

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-3">
          <h1 className="text-base font-semibold text-slate-900">{title}</h1>
          <div className="flex items-center gap-2">
            {user && <Avatar name={user.display_name} size={32} />}
            <button
              onClick={onLogout}
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 active:bg-slate-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className={`mx-auto w-full max-w-3xl flex-1 px-4 py-4 ${showBottomNav ? "pb-24" : "pb-8"}`}>
        {children}
      </main>

      {showBottomNav && (
        <nav
          className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white"
          style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
        >
          <div className="mx-auto flex max-w-3xl">
            {tabs.map((tab) => {
              const active = isActive(tab.to);
              return (
                <Link
                  key={tab.to}
                  to={tab.to}
                  className={`flex flex-1 flex-col items-center gap-0.5 py-2.5 text-xs font-medium ${
                    active ? "text-indigo-600" : "text-slate-500"
                  }`}
                >
                  <tab.icon active={active} />
                  {tab.label}
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
