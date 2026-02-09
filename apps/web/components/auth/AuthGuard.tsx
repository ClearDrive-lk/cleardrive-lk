"use client";

import { useEffect, useState } from "react";
import { useAppSelector, useAppDispatch } from "@/lib/store/store";
import { setCredentials } from "@/lib/store/features/auth/authSlice";
import { useRouter } from "next/navigation";

/**
 * AuthGuard Component
 * Silent check - no "Checking authentication..." message
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      // 1. If Redux says we are authenticated, we are good
      if (isAuthenticated) {
        setIsChecking(false);
        return;
      }

      // 2. If Redux checks fail, check for cookie (persistence)
      const hasCookie = document.cookie.includes("access_token=");

      if (hasCookie) {
        // Restore session (Hydration)
        // In a real app, you would fetch /me endpoint here
        // For now, we restore from what we have or a placeholder

        dispatch(
          setCredentials({
            user: {
              id: "USR-8829-XJ",
              email: "agent@cleardrive.lk",
              name: "Agent",
              role: "admin",
            },
            token: "restored-session",
          }),
        );
        setIsChecking(false);
      } else {
        // No cookie, no state -> Redirect
        router.push("/login");
      }
    };

    checkAuth();
  }, [isAuthenticated, dispatch, router]);

  // Don't render anything while checking to avoid flash
  if (isChecking) {
    return null;
  }

  return <>{children}</>;
}
