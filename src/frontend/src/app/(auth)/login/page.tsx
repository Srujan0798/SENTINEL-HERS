"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth, formatApiError } from "@/lib/auth";

const DEMO_EMAIL = "demo@sentinel.io";
const DEMO_PASSWORD = "Sentinel2026!";

function LoginForm() {
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const goAfterLogin = () => {
    window.location.assign(redirectTo.startsWith("/") ? redirectTo : "/dashboard");
  };

  const runLogin = async (e?: string, p?: string) => {
    setError("");
    setIsLoading(true);
    const em = (e ?? email).trim();
    const pw = p ?? password;
    try {
      await login({ email: em, password: pw });
      goAfterLogin();
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : formatApiError(err, "Login failed — check email/password and API URL");
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Radar ring signature */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-40"
      >
        <div className="h-[min(80vw,520px)] w-[min(80vw,520px)] rounded-full border border-[color:var(--line)]" />
        <div className="absolute h-[min(55vw,360px)] w-[min(55vw,360px)] rounded-full border border-[color:var(--phosphor)]/20" />
        <div className="absolute h-[min(30vw,200px)] w-[min(30vw,200px)] rounded-full border border-[color:var(--ice)]/15" />
      </div>

      <Card className="w-full max-w-md relative z-10 border-[color:var(--line)] bg-[color:var(--panel)]/95 shadow-[0_0_60px_rgba(232,168,56,0.08)]">
        <CardHeader className="text-center space-y-2 pb-2">
          <p className="label-caps text-[color:var(--phosphor)]">SENTINEL</p>
          <CardTitle className="text-2xl font-display font-semibold tracking-tight">
            Mission console
          </CardTitle>
          <CardDescription className="text-[color:var(--ink-muted)]">
            One workspace for incidents, signal, and AI-assisted response.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(ev) => {
              ev.preventDefault();
              void runLogin();
            }}
            className="space-y-4"
          >
            {error && (
              <div
                className="p-3 text-sm text-[color:var(--destructive-foreground)] bg-[color:var(--sev1)]/15 border border-[color:var(--sev1)]/40 rounded-md whitespace-pre-wrap font-data text-xs"
                role="alert"
              >
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="label-caps">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 border border-[color:var(--line)] rounded-md bg-[color:var(--void)] text-[color:var(--ink)] focus:outline-none focus:ring-2 focus:ring-[color:var(--ice)] disabled:opacity-50"
                placeholder="demo@sentinel.io"
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="label-caps">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2.5 border border-[color:var(--line)] rounded-md bg-[color:var(--void)] text-[color:var(--ink)] focus:outline-none focus:ring-2 focus:ring-[color:var(--ice)] disabled:opacity-50"
                placeholder="••••••••"
                required
                disabled={isLoading}
              />
            </div>

            <Button type="submit" className="w-full h-11 font-semibold" disabled={isLoading}>
              {isLoading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="mt-5 rounded-md border border-[color:var(--phosphor)]/35 bg-[color:var(--phosphor)]/8 p-4 text-sm">
            <p className="font-semibold text-[color:var(--phosphor)] mb-1">Judge demo — one click</p>
            <p className="text-[color:var(--ink-muted)] text-xs mb-3 font-data">
              {DEMO_EMAIL}
              <br />
              {DEMO_PASSWORD}
            </p>
            <Button
              type="button"
              className="w-full h-11 font-semibold"
              disabled={isLoading}
              onClick={() => {
                setEmail(DEMO_EMAIL);
                setPassword(DEMO_PASSWORD);
                void runLogin(DEMO_EMAIL, DEMO_PASSWORD);
              }}
            >
              {isLoading ? "Opening console…" : "▶ Enter live SEV1 demo"}
            </Button>
          </div>

          <div className="mt-6 text-center text-sm text-[color:var(--ink-muted)]">
            No account?{" "}
            <Link href="/register" className="text-[color:var(--ice)] hover:underline font-medium">
              Create one
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-[color:var(--ink-muted)]">
          Loading console…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
