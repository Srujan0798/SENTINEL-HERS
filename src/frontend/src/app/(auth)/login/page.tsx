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
    // Full page navigation so middleware always sees cookies on the next request.
    // (client router.push alone caused "login then bounce" for judges.)
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await runLogin();
  };

  const handleDemoLogin = async () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    await runLogin(DEMO_EMAIL, DEMO_PASSWORD);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4 py-12">
      <Card className="w-full max-w-md border-zinc-800 bg-zinc-900 text-zinc-50 shadow-2xl">
        <CardHeader className="text-center space-y-2">
          <p className="text-xs font-semibold tracking-[0.2em] text-emerald-400 uppercase">
            SENTINEL
          </p>
          <CardTitle className="text-2xl font-bold text-white">Sign in</CardTitle>
          <CardDescription className="text-zinc-400">
            AI-native engineering operations — live demo ready for judges
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div
                className="p-3 text-sm text-red-200 bg-red-950/60 border border-red-800 rounded-md whitespace-pre-wrap"
                role="alert"
              >
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-zinc-200">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-zinc-700 rounded-md bg-zinc-950 text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
                placeholder="demo@sentinel.io"
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-zinc-200">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-zinc-700 rounded-md bg-zinc-950 text-zinc-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
                placeholder="••••••••"
                required
                disabled={isLoading}
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white"
              disabled={isLoading}
            >
              {isLoading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="mt-5 rounded-md border border-emerald-800/60 bg-emerald-950/40 p-4 text-sm">
            <p className="font-semibold text-emerald-300 mb-1">Judge demo — one click</p>
            <p className="text-zinc-400 text-xs mb-3">
              {DEMO_EMAIL} · {DEMO_PASSWORD}
              <br />
              Opens SEV1 war room (AI, timeline, tasks, SLA, comms).
            </p>
            <Button
              type="button"
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold"
              disabled={isLoading}
              onClick={() => void handleDemoLogin()}
            >
              {isLoading ? "Signing in as demo…" : "▶ Enter as demo@sentinel.io"}
            </Button>
          </div>

          <div className="mt-6 text-center text-sm text-zinc-500">
            No account?{" "}
            <Link href="/register" className="text-emerald-400 hover:underline font-medium">
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
        <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-400">
          Loading login…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
