"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth, useRole } from "@/lib/auth";
import { StatusBar } from "@/components/realtime/StatusBar";
import { Menu, X } from "lucide-react";

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (mounted && !state.isLoading && !state.isAuthenticated && !state.accessToken) {
      router.replace("/login");
    }
  }, [mounted, state.isLoading, state.isAuthenticated, state.accessToken, router]);

  const effectiveRole = role || "operator";

  const handleLogout = async () => {
    await logout();
    window.location.assign("/login");
  };

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground font-data text-sm">
        Loading console…
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-background/90 backdrop-blur-md sticky top-0 z-50">
        <div className="flex h-14 sm:h-16 items-center justify-between px-3 sm:px-4 gap-2 max-w-7xl mx-auto">
          <Link href="/dashboard" className="flex items-center gap-2 shrink-0 group">
            <span className="h-2 w-2 rounded-full bg-primary group-hover:shadow-[0_0_12px_hsl(var(--primary))] transition-shadow" />
            <span className="text-base sm:text-lg font-display font-semibold tracking-tight">
              SENTINEL
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-2 sm:gap-3 min-w-0 flex-1 justify-end">
            <ul className="flex items-center gap-0.5 sm:gap-1">
              {navigation.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <li key={item.name} className="shrink-0">
                    <Link
                      href={item.href}
                      className={`text-xs sm:text-sm font-medium whitespace-nowrap px-2.5 py-1.5 rounded-md transition-colors ${
                        active
                          ? "text-primary-foreground bg-primary"
                          : "text-muted-foreground hover:text-foreground hover:bg-accent"
                      }`}
                    >
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="flex items-center gap-2 sm:gap-3 shrink-0 border-l border-border pl-2 sm:pl-3">
              <StatusBar teamId={state.user?.team_id} />
              <span className="text-[10px] sm:text-xs font-data text-muted-foreground hidden lg:block max-w-[11rem] truncate">
                {state.user?.name || "Operator"}
                <span className="text-primary"> · {effectiveRole}</span>
              </span>
              <Button variant="ghost" size="sm" className="text-xs" onClick={() => void handleLogout()}>
                Log out
              </Button>
            </div>
          </nav>

          {/* Mobile hamburger */}
          <div className="flex md:hidden items-center gap-2">
            <StatusBar teamId={state.user?.team_id} />
            <button
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="h-10 w-10 flex items-center justify-center rounded-md hover:bg-accent"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav panel */}
        {mobileMenuOpen && (
          <nav className="md:hidden border-t border-border bg-background animate-in slide-in-from-top duration-200">
            <ul className="flex flex-col py-2 px-3">
              {navigation.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <li key={item.name}>
                    <Link
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center h-11 px-3 rounded-md text-sm font-medium transition-colors ${
                        active
                          ? "text-primary-foreground bg-primary"
                          : "text-muted-foreground hover:text-foreground hover:bg-accent"
                      }`}
                    >
                      {item.name}
                    </Link>
                  </li>
                );
              })}
              <li className="border-t border-border mt-2 pt-2">
                <div className="flex items-center justify-between px-3 h-11">
                  <span className="text-xs text-muted-foreground truncate max-w-[50%]">
                    {state.user?.name || "Operator"}
                    <span className="text-primary"> · {effectiveRole}</span>
                  </span>
                  <Button variant="ghost" size="sm" className="text-xs" onClick={() => void handleLogout()}>
                    Log out
                  </Button>
                </div>
              </li>
            </ul>
          </nav>
        )}
      </header>

      <main className="max-w-7xl mx-auto py-4 sm:py-6 px-3 sm:px-4">{children}</main>
    </div>
  );
}
