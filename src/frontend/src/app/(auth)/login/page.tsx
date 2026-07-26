"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Copy, Check, AlertCircle, Eye, EyeOff } from "lucide-react";
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
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const goAfterLogin = () => {
    window.location.assign(redirectTo.startsWith("/") ? redirectTo : "/dashboard");
  };

  const calculateStrength = (pwd: string): number => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[a-z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return Math.min(score, 4);
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setPassword(val);
    setPasswordStrength(calculateStrength(val));
  };

  const runLogin = async (em?: string, pw?: string) => {
    setError("");
    setIsLoading(true);
    const loginEmail = (em ?? email).trim();
    const loginPassword = pw ?? password;
    try {
      await login({ email: loginEmail, password: loginPassword });
      goAfterLogin();
    } catch (err) {
      const msg = err instanceof Error
        ? err.message
        : formatApiError(err, "Login failed — check email/password and API URL");
      setError(msg);
      setIsLoading(false);
    }
  };

  const handleDemoLogin = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setPasswordStrength(4);
    void runLogin(DEMO_EMAIL, DEMO_PASSWORD);
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-40">
        <div className="h-[min(80vw,520px)] w-[min(80vw,520px)] rounded-full border border-[color:var(--line)]" />
        <div className="absolute h-[min(55vw,360px)] w-[min(55vw,360px)] rounded-full border border-[color:var(--phosphor)]/20" />
        <div className="absolute h-[min(30vw,200px)] w-[min(30vw,200px)] rounded-full border border-[color:var(--ice)]/15" />
      </div>

      <Card className="w-full max-w-md relative z-10 border-[color:var(--line)] bg-[color:var(--panel)]/95 shadow-[0_0_60px_rgba(232,168,56,0.08)]">
        <CardHeader className="text-center space-y-2 pb-2">
          <p className="label-caps text-[color:var(--phosphor)]">SENTINEL</p>
          <CardTitle className="text-2xl font-display font-semibold tracking-tight">Mission console</CardTitle>
          <CardDescription className="text-[color:var(--ink-muted)]">
            One workspace for incidents, signal, and AI-assisted response.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(ev) => { ev.preventDefault(); void runLogin(); }} className="space-y-4">
            {error && (
              <div
                className="flex items-start gap-2 p-3 text-sm text-[color:var(--destructive-foreground)] bg-[color:var(--sev1)]/15 border border-[color:var(--sev1)]/40 rounded-md whitespace-pre-wrap font-data text-xs"
                role="alert"
              >
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => setError("")}
                  className="ml-auto text-[color:var(--sev1)] hover:text-[color:var(--destructive-foreground)] p-1"
                  aria-label="Dismiss error"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="label-caps">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full"
                placeholder="demo@sentinel.io"
                required
                disabled={isLoading}
                aria-describedby={error ? "login-error" : undefined}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="label-caps mb-0">Password</Label>
                <span className="text-xs text-[color:var(--ink-muted)] font-data">
                  {passwordStrength}/4 strength
                </span>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={handlePasswordChange}
                  className="w-full pr-12"
                  placeholder="••••••••"
                  required
                  disabled={isLoading}
                  aria-describedby={error ? "login-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[color:var(--ink-muted)] hover:text-[color:var(--ink)] p-1"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="h-1.5 bg-[color:var(--line)] rounded-full overflow-hidden" role="progressbar" aria-valuenow={passwordStrength} aria-valuemin={0} aria-valuemax={4} aria-label="Password strength">
                <div
                  className={`h-full transition-all duration-200 rounded-full ${
                    passwordStrength === 0 ? "w-0" :
                    passwordStrength === 1 ? "w-1/4 bg-[color:var(--sev1)]" :
                    passwordStrength === 2 ? "w-1/2 bg-[color:var(--warn)]" :
                    passwordStrength === 3 ? "w-3/4 bg-[color:var(--phosphor)]" :
                    "w-full bg-[color:var(--ok)]"
                  }`}
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-11 font-semibold" disabled={isLoading}>
              {isLoading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <Separator className="my-5" />

          <div className="rounded-md border border-[color:var(--phosphor)]/35 bg-[color:var(--phosphor)]/8 p-4 text-sm">
            <p className="font-semibold text-[color:var(--phosphor)] mb-1">Judge demo — one click</p>
            <div className="flex flex-col gap-2 text-xs mb-3 font-data">
              <div className="flex items-center gap-2 text-[color:var(--ink-muted)]">
                <span className="font-data">{DEMO_EMAIL}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 p-0"
                  onClick={() => copyToClipboard(DEMO_EMAIL, "Email")}
                  aria-label="Copy email"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
              <div className="flex items-center gap-2 text-[color:var(--ink-muted)]">
                <span className="font-data">{DEMO_PASSWORD}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 p-0"
                  onClick={() => copyToClipboard(DEMO_PASSWORD, "Password")}
                  aria-label="Copy password"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <Button
              type="button"
              className="w-full h-11 font-semibold"
              disabled={isLoading}
              onClick={handleDemoLogin}
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

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-xs text-[color:var(--ink-muted)] font-data">
        Built for METIS Hard Track — SENTINEL AI-Native EngOps
      </div>
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