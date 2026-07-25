import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/register"];

function isPublicPath(path: string): boolean {
  return PUBLIC_PATHS.some((p) => path === p || path.startsWith(`${p}/`) || path.startsWith(`${p}?`));
}

function isAuthPath(path: string): boolean {
  return path === "/login" || path === "/register" || path.startsWith("/login?") || path.startsWith("/register?");
}

function hasSession(request: NextRequest): boolean {
  // Prefer tiny session flag (reliable). Fall back to access_token cookie.
  const flag = request.cookies.get("sentinel_session")?.value;
  if (flag === "1" || flag === "true") return true;
  const access = request.cookies.get("access_token")?.value;
  const refresh = request.cookies.get("refresh_token")?.value;
  return Boolean(access || refresh);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Never gate Next internals / static
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const authed = hasSession(request);

  if (isPublicPath(pathname)) {
    // Already signed in → skip login form
    if (isAuthPath(pathname) && authed) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    return NextResponse.next();
  }

  if (!authed) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|gif|svg|ico|webp)$).*)"],
};
