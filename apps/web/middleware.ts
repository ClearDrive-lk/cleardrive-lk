import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 1. Define which routes are protected
const protectedRoutes = ["/dashboard", "/profile", "/orders"];
const authRoutes = ["/login", "/verify-otp"];

export function middleware(request: NextRequest) {
  // 2. Check for the session token (we will use a cookie later, assuming 'access_token' for now)
  // Note: Middleware can only read Cookies, not LocalStorage.
  // We will update the login logic to set a cookie in CD-354.
  const token = request.cookies.get("access_token")?.value;

  const { pathname } = request.nextUrl;

  // 3. Scenario: User IS NOT logged in
  if (!token) {
    // If they try to visit a protected page -> Kick them to login
    if (protectedRoutes.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  // 4. Scenario: User IS logged in
  if (token) {
    // If they try to visit login or OTP -> Send them to dashboard
    if (authRoutes.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

// 5. Configure which paths the middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
