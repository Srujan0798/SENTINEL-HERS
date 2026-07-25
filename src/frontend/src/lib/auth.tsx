"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://localhost:8000";

export interface Role {
  id: string;
  name: string;
  permissions: string[];
  description: string;
}

export interface User {
  id: string;
  team_id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  role_id: string;
  role?: Role | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  team_name: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: true,
  isAuthenticated: false,
};

// Session cookie is a tiny route-guard flag for Next middleware.
// Full JWTs live in localStorage (and a short-lived access cookie when size allows).
// Middleware only needs to know "has session" — API still validates Bearer JWT.
const SESSION_FLAG = "sentinel_session";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

function cookieBase(): string {
  const secure = typeof window !== "undefined" && window.location.protocol === "https:";
  return `path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax${secure ? "; Secure" : ""}`;
}

function setCookie(name: string, value: string) {
  // Encode so JWT characters never break the Set-Cookie parser.
  document.cookie = `${name}=${encodeURIComponent(value)}; ${cookieBase()}`;
}

function clearCookie(name: string) {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
}

/** Normalize FastAPI error bodies into a human string (not "[object Object]"). */
export function formatApiError(detail: unknown, fallback = "Request failed"): string {
  if (detail == null) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (typeof detail === "object" && detail !== null && "detail" in detail) {
    return formatApiError((detail as { detail: unknown }).detail, fallback);
  }
  try {
    return JSON.stringify(detail);
  } catch {
    return fallback;
  }
}

function persistTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
  localStorage.setItem("sentinel_token", accessToken);
  // Tiny flag middleware always accepts (avoids cookie size / parse edge cases).
  setCookie(SESSION_FLAG, "1");
  // Also store tokens for any code reading cookies; encode for safety.
  setCookie("access_token", accessToken);
  setCookie("refresh_token", refreshToken);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("sentinel_token");
  clearCookie(SESSION_FLAG);
  clearCookie("access_token");
  clearCookie("refresh_token");
}

const AuthContext = createContext<{
  state: AuthState;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
} | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);

  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      if (accessToken && refreshToken) {
        // Re-assert session cookie so middleware stays happy after hard refresh.
        setCookie(SESSION_FLAG, "1");
        setState((prev) => ({ ...prev, accessToken, refreshToken }));
        try {
          await fetchUser(accessToken);
        } catch {
          try {
            await refreshAccessToken();
          } catch {
            clearTokens();
            setState({ ...initialState, isLoading: false });
          }
        }
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    void initAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchUser = async (token: string) => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch user");
    }

    const user = (await response.json()) as User;
    setState((prev) => ({
      ...prev,
      user,
      isAuthenticated: true,
      isLoading: false,
    }));
  };

  const login = async (credentials: LoginRequest) => {
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
    } catch {
      throw new Error(
        `Cannot reach API at ${API_BASE}. Check NEXT_PUBLIC_API_BASE_URL and CORS.`
      );
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(formatApiError(error, `Login failed (${response.status})`));
    }

    const data: LoginResponse = await response.json();
    if (!data.access_token || !data.refresh_token) {
      throw new Error("Login response missing tokens");
    }
    persistTokens(data.access_token, data.refresh_token);

    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const register = async (data: RegisterRequest) => {
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    } catch {
      throw new Error(
        `Cannot reach API at ${API_BASE}. Check NEXT_PUBLIC_API_BASE_URL and CORS.`
      );
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(formatApiError(error, `Registration failed (${response.status})`));
    }

    const result: LoginResponse = await response.json();
    persistTokens(result.access_token, result.refresh_token);

    setState({
      user: result.user,
      accessToken: result.access_token,
      refreshToken: result.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      clearTokens();
      setState({ ...initialState, isLoading: false });
      return;
    }

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      setState({ ...initialState, isLoading: false });
      return;
    }

    const data: LoginResponse = await response.json();
    persistTokens(data.access_token, data.refresh_token);

    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const logout = async () => {
    clearTokens();
    setState({ ...initialState, isLoading: false });
  };

  return (
    <AuthContext.Provider value={{ state, login, register, logout, refreshAccessToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function useUser(): User | null {
  const { state } = useAuth();
  return state.user;
}

function roleFromJwt(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const padded = part.replace(/-/g, "+").replace(/_/g, "/");
    const pad = padded.length % 4 === 0 ? "" : "=".repeat(4 - (padded.length % 4));
    const payload = JSON.parse(atob(padded + pad)) as { role?: unknown };
    if (typeof payload.role === "string" && payload.role && !payload.role.includes("-")) {
      return payload.role;
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function useRole(): string | null {
  const user = useUser();
  return user?.role?.name ?? roleFromJwt() ?? null;
}

export function useHasPermission(permission: string): boolean {
  const user = useUser();
  if (!user?.role?.permissions) return false;
  if (user.role.permissions.includes("*")) return true;
  return user.role.permissions.includes(permission);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
}

export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  headers.set("Content-Type", "application/json");

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    const refreshToken =
      typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    if (refreshToken) {
      const refreshed = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshed.ok) {
        const data = await refreshed.json();
        persistTokens(data.access_token, data.refresh_token);
        headers.set("Authorization", `Bearer ${data.access_token}`);
        response = await fetch(url, { ...options, headers });
      }
    }
  }

  return response;
}

export { API_BASE as AUTH_API_BASE };
