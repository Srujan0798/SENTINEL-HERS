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
  role: Role;
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

export interface RefreshRequest {
  refresh_token: string;
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

const AuthContext = createContext<{
  state: AuthState;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
}>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);

  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      if (accessToken && refreshToken) {
        setState((prev) => ({ ...prev, accessToken, refreshToken }));
        try {
          await fetchUser(accessToken);
        } catch {
          await refreshAccessToken();
        }
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    initAuth();
  }, []);

  const fetchUser = async (token: string) => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch user");
    }

    const user = await response.json();
    setState((prev) => ({
      ...prev,
      user,
      isAuthenticated: true,
      isLoading: false,
    }));
  };

  const login = async (credentials: LoginRequest) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data: LoginResponse = await response.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const register = async (data: RegisterRequest) => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Registration failed");
    }

    const result: LoginResponse = await response.json();
    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("refresh_token", result.refresh_token);

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
      setState(initialState);
      return;
    }

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setState(initialState);
      return;
    }

    const data: LoginResponse = await response.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const logout = async () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setState(initialState);
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

export function useRole(): string | null {
  const user = useUser();
  return user?.role?.name ?? null;
}

export function useHasPermission(permission: string): boolean {
  const user = useUser();
  if (!user?.role?.permissions) return false;
  if (user.role.permissions.includes("*")) return true;
  return user.role.permissions.includes(permission);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  headers.set("Content-Type", "application/json");

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    if (refreshToken) {
      const refreshed = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshed.ok) {
        const data = await refreshed.json();
        localStorage.setItem("access_token", data.access_token);
        headers.set("Authorization", `Bearer ${data.access_token}`);
        response = await fetch(url, { ...options, headers });
      }
    }
  }

  return response;
}