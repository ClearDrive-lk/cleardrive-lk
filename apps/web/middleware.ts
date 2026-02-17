import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 1. Define which routes are protected
const protectedRoutes = ["/dashboard", "/profile", "/orders", "/vehicles"];
const authRoutes = ["/login", "/register", "/verify-otp", "/forgot-password"];

export function middleware(request: NextRequest) {
  // 2. Check if we're in development mode
  const isDevelopment = process.env.NODE_ENV === "development";

  // 3. Create the response
  const response = NextResponse.next();

  // Extract backend API origin from NEXT_PUBLIC_API_URL (if valid).
  let apiOrigin = "";
  if (process.env.NEXT_PUBLIC_API_URL) {
    try {
      apiOrigin = new URL(process.env.NEXT_PUBLIC_API_URL).origin;
    } catch {
      apiOrigin = "";
    }
  }

  // 4. Only apply strict CSP in production (development needs inline styles for HMR)
  if (!isDevelopment) {
    // Build Content Security Policy (CSP) header for XSS protection
    const cspHeader = `
      default-src 'self';
      script-src 'self' 'unsafe-inline' https://accounts.google.com https://accounts.gstatic.com https://vercel.live;
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com;
      font-src 'self' https://fonts.gstatic.com;
      img-src 'self' blob: data: https:;
      connect-src 'self' ${apiOrigin} https://accounts.google.com https://oauth2.googleapis.com;
      frame-src 'self' https://accounts.google.com;
      object-src 'none';
      base-uri 'self';
      form-action 'self';
      frame-ancestors 'none';
      upgrade-insecure-requests;
    `
      .replace(/\s{2,}/g, " ")
      .trim();

    // Set CSP and security headers (production only)
    response.headers.set("Content-Security-Policy", cspHeader);
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set("X-Frame-Options", "DENY");
    response.headers.set("X-XSS-Protection", "1; mode=block");
    response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
    response.headers.set(
      "Permissions-Policy",
      "camera=(), microphone=(), geolocation=()",
    );
  }

  // 5. Check for the session token (Refactored to check refresh_token)
  // Since access_token is now in sessionStorage (client-side), we rely on the httpOnly refresh cookie
  const token = request.cookies.get("refresh_token")?.value;

  const { pathname } = request.nextUrl;

  // 6. Scenario: User IS NOT logged in
  if (!token) {
    // If they try to visit a protected page -> Kick them to login
    if (protectedRoutes.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  // 7. Scenario: User IS logged in
  if (token) {
    // If they try to visit login or OTP -> Send them to dashboard
    if (authRoutes.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return response;
}

// 8. Configure which paths the middleware runs on
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
