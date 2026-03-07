"use client";

/**
 * Cookie consent banner.
 * Appears on first visit until user makes a choice.
 *
 * Author: Kalidu
 * Story: CD-101 - Cookie Consent Banner
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  hasConsented,
  acceptAll,
  rejectNonEssential,
  getStoredConsent,
} from "@/lib/cookies/utils";
import { CookieConsent } from "@/lib/cookies/types";

interface CookieBannerProps {
  onConsentChange?: (consent: CookieConsent) => void;
}

export default function CookieBanner({ onConsentChange }: CookieBannerProps) {
  const [visible, setVisible] = useState(false);

  // ===============================================================
  // SHOW BANNER ONLY IF USER HASN'T CONSENTED YET
  // ===============================================================
  useEffect(() => {
    const syncAnalyticsFromConsent = () => {
      const consent = getStoredConsent();
      if (consent?.analytics) {
        loadAnalytics();
      }
    };

    // Returning users with analytics consent should initialize tracking automatically.
    syncAnalyticsFromConsent();
    window.addEventListener(
      "cleardrive:cookie-consent-updated",
      syncAnalyticsFromConsent,
    );

    // Small delay so banner doesn't flash on page load
    const timer = setTimeout(() => {
      if (!hasConsented()) {
        setVisible(true);
      }
    }, 500);

    return () => {
      clearTimeout(timer);
      window.removeEventListener(
        "cleardrive:cookie-consent-updated",
        syncAnalyticsFromConsent,
      );
    };
  }, []);

  // ===============================================================
  // HANDLE ACCEPT ALL (CD-101.2)
  // ===============================================================
  const handleAcceptAll = () => {
    acceptAll(); // Save to localStorage (CD-101.3)
    setVisible(false);
    loadAnalytics(); // Load analytics (CD-101.4)

    const consent = getStoredConsent();
    if (consent && onConsentChange) {
      onConsentChange(consent);
    }
  };

  // ===============================================================
  // HANDLE REJECT NON-ESSENTIAL (CD-101.2)
  // ===============================================================
  const handleRejectNonEssential = () => {
    rejectNonEssential(); // Save to localStorage (CD-101.3)
    setVisible(false);
    // Analytics NOT loaded

    const consent = getStoredConsent();
    if (consent && onConsentChange) {
      onConsentChange(consent);
    }
  };

  // ===============================================================
  // LOAD ANALYTICS IF ACCEPTED (CD-101.4)
  // ===============================================================
  const loadAnalytics = () => {
    const gaId = process.env.NEXT_PUBLIC_GA_ID;
    if (typeof window === "undefined" || !gaId) return;

    // Prevent duplicate script injection on repeated renders/navigation.
    if (document.getElementById("ga-script")) {
      window.gtag?.("config", gaId);
      return;
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag =
      window.gtag ||
      ((...args: unknown[]) => {
        window.dataLayer?.push(args);
      });

    window.gtag("js", new Date());
    window.gtag("config", gaId);

    const script = document.createElement("script");
    script.id = "ga-script";
    script.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`;
    script.async = true;
    document.head.appendChild(script);
  };

  // Don't render if user already consented
  if (!visible) return null;

  return (
    <>
      {/* ============================================================
          BACKDROP (subtle overlay)
          ============================================================ */}
      <div className="fixed inset-0 bg-black/20 z-40 pointer-events-none" />

      {/* ============================================================
          COOKIE BANNER
          ============================================================ */}
      <div
        className="
          fixed bottom-0 left-0 right-0 z-50
          bg-white border-t-2 border-gray-200
          shadow-2xl
          animate-in slide-in-from-bottom
          duration-300
        "
        role="dialog"
        aria-label="Cookie consent"
        aria-modal="false"
      >
        <div className="max-w-7xl mx-auto px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            {/* Cookie Icon + Text */}
            <div className="flex items-start gap-3 flex-1">
              <span
                className="text-3xl flex-shrink-0 mt-0.5"
                aria-hidden="true"
              >
                {"\u{1F36A}"}
              </span>

              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  We use cookies
                </h2>
                <p className="text-sm text-gray-600 mt-0.5 leading-relaxed">
                  We use cookies to improve your experience, analyse traffic,
                  and show relevant content. Essential cookies are always
                  active.{" "}
                  <Link
                    href="/api/v1/gdpr/cookie-policy"
                    target="_blank"
                    className="text-blue-600 underline hover:text-blue-800"
                  >
                    Cookie Policy
                  </Link>
                  {" · "}
                  <Link
                    href="/api/v1/gdpr/privacy-policy"
                    target="_blank"
                    className="text-blue-600 underline hover:text-blue-800"
                  >
                    Privacy Policy
                  </Link>
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col xs:flex-row items-stretch xs:items-center gap-2 w-full sm:w-auto flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRejectNonEssential}
                className="text-sm border-gray-300 hover:border-gray-400 whitespace-nowrap"
              >
                Reject Non-Essential
              </Button>

              <Link href="/cookie-preferences">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-sm border-gray-300 hover:border-gray-400 w-full whitespace-nowrap"
                >
                  Customize
                </Button>
              </Link>

              <Button
                size="sm"
                onClick={handleAcceptAll}
                className="text-sm bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
              >
                Accept All
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
