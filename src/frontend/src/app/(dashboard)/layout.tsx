"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth, useRole } from "@/lib/auth";
import { StatusBar } from "@/components/realtime/StatusBar";

const navigation = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Incidents", href: "/incidents" },
  { name: "Monitoring", href: "/monitoring" },
  { name: "Deployments", href: "/deployments" },
  { name: "Analytics", href: "/analytics" },
  { name: "Settings", href: "/settings" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { state, logout } = useAuth();
  const role = useRole();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const effectiveRole = role || "operator";

  const handleLogout = async () => {
    await logout();
    window.location.assign("/login");
  };

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[color:var(--ink-muted)] font-data text-sm">
        Loading console…
      </div>
    );
  }

  if (!state.isLoading && !state.isAuthenticated && !state.accessToken) {
    if (typeof window !== "undefined") router.replace("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[color:var(--line)] bg-[color:var(--panel)]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-4 gap-2 max-w-7xl mx-auto">
          <Link href="/dashboard" className="flex items-center gap-2 shrink-0 group">
            <span className="h-2 w-2 rounded-full bg-[color:var(--phosphor)] group-hover:shadow-[0_0_12px_var(--phosphor)] transition-shadow" />
            <span className="text-base sm:text-lg font-display font-semibold tracking-tight text-[color:var(--ink)]">
              SENTINEL
            </span>
          </Link>

          <nav className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1 justify-end">
            <ul className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto max-w-[58vw] sm:max-w-none py-1">
              {navigation.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <li key={item.name} className="shrink-0">
                    <Link
                      href={item.href}
                      className={`text-xs sm:text-sm font-medium whitespace-nowrap px-2.5 py-1.5 rounded-md transition-colors ${
                        active
                          ? "text-[color:var(--primary-foreground)] bg-[color:var(--phosphor)]"
                          : "text-[color:var(--ink-muted)] hover:text-[color:var(--ink)] hover:bg-[color:var(--panel-elevated)]"
                      }`}
                    >
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="flex items-center gap-2 sm:gap-3 shrink-0 border-l border-[color:var(--line)] pl-2 sm:pl-3">
              <StatusBar teamId={state.user?.team_id} />
              <span className="text-[10px] sm:text-xs font-data text-[color:var(--ink-muted)] hidden md:block max-w-[11rem] truncate">
                {state.user?.name || "Operator"}
                <span className="text-[color:var(--phosphor)]"> · {effectiveRole}</span>
              </span>
              <Button variant="ghost" size="sm" className="text-xs" onClick={() => void handleLogout()}>
                Log out
              </Button>
            </div>
          </nav>
        </div>
      </header>

      <main className="container max-w-7xl mx-auto py-4 sm:py-6 px-3 sm:px-4">{children}</main>
    </div>
  );
}
