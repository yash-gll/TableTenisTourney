import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { Avatar } from "./Avatar";
import { Button } from "./ui";

export function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="font-bold text-indigo-700">
          🏓 TT Tournaments
        </Link>
        <div className="flex items-center gap-3">
          {user?.role !== "PLAYER" && (
            <Link to="/admin" className="text-sm text-slate-600 hover:underline">
              Admin
            </Link>
          )}
          {user && <Avatar name={user.display_name} size={36} />}
          <Button variant="secondary" onClick={onLogout}>
            Log out
          </Button>
        </div>
      </div>
    </header>
  );
}
