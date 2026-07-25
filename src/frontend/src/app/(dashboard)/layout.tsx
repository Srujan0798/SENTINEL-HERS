"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth, useRole } from "@/lib/auth";
import { StatusBar } from "@/components/realtime/StatusBar";

const navigation = [
  { name: "Dashboard", href: "/dashboard", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Incidents", href: "/incidents", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Monitoring", href: "/monitoring", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Deployments", href: "/deployments", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Analytics", href: "/analytics", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Settings", href: "/settings", roles: ["admin", "incident_commander", "responder", "viewer"] },
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

  // Never hide the entire product because role hydration lagged — that looked like a broken login.
  const effectiveRole = role || "admin";
  const filteredNav = navigation.filter((item) => item.roles.includes(effectiveRole));

  const handleLogout = async () => {
    await logout();
    window.location.assign("/login");
  };

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-muted-foreground">
        Loading SENTINEL…
      </div>
    );
  }

  if (!state.isLoading && !state.isAuthenticated && !state.accessToken) {
    // Client-side fallback if middleware cookie was lost but user hit a protected shell.
    if (typeof window !== "undefined") {
      router.replace("/login");
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-4 gap-2">
          <Link href="/dashboard" className="text-lg sm:text-xl font-bold text-primary shrink-0">
            SENTINEL
          </Link>

          <nav className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1 justify-end">
            <ul className="flex items-center gap-1 sm:gap-3 overflow-x-auto max-w-[55vw] sm:max-w-none py-1">
              {filteredNav.map((item) => (
                <li key={item.name} className="shrink-0">
                  <Link
                    href={item.href}
                    className={`text-xs sm:text-sm font-medium whitespace-nowrap px-1.5 py-1 rounded transition-colors ${
                      pathname === item.href || pathname.startsWith(item.href + "/")
                        ? "text-primary bg-primary/10"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="flex items-center gap-2 sm:gap-3 shrink-0 border-l pl-2 sm:pl-3">
              <StatusBar teamId={state.user?.team_id} />
              <span className="text-xs text-muted-foreground hidden md:block max-w-[10rem] truncate">
                {state.user?.name || "Operator"} · {effectiveRole}
              </span>
              <Button variant="ghost" size="sm" onClick={() => void handleLogout()}>
                Log out
              </Button>
            </div>
          </nav>
        </div>
      </header>

      <main className="container py-4 sm:py-6 px-3 sm:px-4">{children}</main>
    </div>
  );
}
