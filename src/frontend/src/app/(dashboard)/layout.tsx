"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth, useRole } from "@/lib/auth";
import { StatusBar } from "@/components/realtime/StatusBar";

const navigation = [
  { name: "Dashboard", href: "/dashboard", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Incidents", href: "/incidents", roles: ["admin", "incident_commander", "responder", "viewer"] },
  { name: "Monitoring", href: "/monitoring", roles: ["admin", "incident_commander", "responder"] },
  { name: "Deployments", href: "/deployments", roles: ["admin", "incident_commander", "responder"] },
  { name: "Analytics", href: "/analytics", roles: ["admin", "incident_commander"] },
  { name: "Settings", href: "/settings", roles: ["admin"] },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { state, logout } = useAuth();
  const role = useRole();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const filteredNav = navigation.filter((item) => item.roles.includes(role || ""));

  const handleLogout = async () => {
    await logout();
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between px-4">
          <Link href="/dashboard" className="text-xl font-bold text-primary">
            SENTINEL
          </Link>

          <nav className="flex items-center gap-6">
            <ul className="flex items-center gap-4">
              {filteredNav.map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={`text-sm font-medium transition-colors hover:text-primary ${
                      pathname === item.href
                        ? "text-primary"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="flex items-center gap-4">
              <StatusBar teamId={state.user?.team_id} />
              <span className="text-sm text-muted-foreground hidden sm:block">
                {state.user?.name} ({role})
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </div>
          </nav>
        </div>
      </header>

      <main className="container py-6 px-4">{children}</main>
    </div>
  );
}