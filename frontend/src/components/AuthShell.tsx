import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Card } from "./ui";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="flex min-h-dvh items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-6 block text-center text-xl font-bold text-indigo-700">
          🏓 TT Tournaments
        </Link>
        <Card>
          <h1 className="text-lg font-semibold">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-4 space-y-4">{children}</div>
        </Card>
        {footer && <div className="mt-4 text-center text-sm text-slate-600">{footer}</div>}
      </div>
    </div>
  );
}
