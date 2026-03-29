"use client";

/**
 * Cookie consent banner.
 * Appears on first visit until user makes a choice.
 *
 * Author: Kalidu
 * Story: CD-101 - Cookie Consent Banner
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  acceptAll,
  getStoredConsent,
  hasConsented,
  rejectNonEssential,
} from "@/lib/cookies/utils";
import { CookieConsent } from "@/lib/cookies/types";
import { getSriAttributes } from "@/lib/sri";

interface CookieBannerProps {
  onConsentChange?: (consent: CookieConsent) => void;
}

export default function CookieBanner({ onConsentChange }: CookieBannerProps) {
  const [visible, setVisible] = useState(false);

  const loadAnalytics = () => {
    const gaId = process.env.NEXT_PUBLIC_GA_ID;
    if (typeof window === "undefined" || !gaId) return;

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
    const { integrity, crossOrigin } = getSriAttributes(script.src);
    if (integrity) {
      script.integrity = integrity;
      script.crossOrigin = crossOrigin ?? "anonymous";
    }
    script.async = true;
    document.head.appendChild(script);
  };

  useEffect(() => {
    const syncAnalyticsFromConsent = () => {
      const consent = getStoredConsent();
      if (consent?.analytics) {
        loadAnalytics();
      }
    };

    syncAnalyticsFromConsent();
    window.addEventListener(
      "cleardrive:cookie-consent-updated",
      syncAnalyticsFromConsent,
    );

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

  const handleAcceptAll = () => {
    acceptAll();
    setVisible(false);
    loadAnalytics();

    const consent = getStoredConsent();
    if (consent && onConsentChange) {
      onConsentChange(consent);
    }
  };

  const handleRejectNonEssential = () => {
    rejectNonEssential();
    setVisible(false);

    const consent = getStoredConsent();
    if (consent && onConsentChange) {
      onConsentChange(consent);
    }
  };

  if (!visible) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 pointer-events-none bg-[#c6c5b9]/35 backdrop-blur-[2px] dark:bg-[#0f1417]/55" />

      <div
        className="fixed inset-x-0 bottom-0 z-50 px-3 pb-3 animate-in slide-in-from-bottom duration-300 sm:px-4 sm:pb-4"
        role="dialog"
        aria-label="Cookie consent"
        aria-modal="false"
      >
        <div className="mx-auto max-w-6xl rounded-[1.6rem] border border-[#546a7b]/50 bg-[#fdfdff]/95 px-4 py-4 shadow-[0_22px_60px_rgba(15,23,42,0.22)] backdrop-blur-xl sm:px-6 sm:py-5 dark:border-[#8fa3b1]/28 dark:bg-[#162028]/94 dark:shadow-[0_24px_70px_rgba(0,0,0,0.4)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
            <div className="flex flex-1 items-start gap-3">
              <div className="mt-0.5 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl border border-[#62929e]/30 bg-[#62929e]/10 text-xl shadow-sm dark:border-[#88d6e4]/25 dark:bg-[#88d6e4]/10">
                <span aria-hidden="true">{"\u{1F36A}"}</span>
              </div>

              <div>
                <h2 className="text-base font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                  We use cookies
                </h2>
                <p className="mt-0.5 text-sm leading-relaxed text-[#546a7b] dark:text-[#bdcad4]">
                  We use cookies to improve your experience, analyse traffic,
                  and show relevant content. Essential cookies are always
                  active.{" "}
                  <Link
                    href="/api/v1/gdpr/cookie-policy"
                    target="_blank"
                    className="text-[#62929e] underline decoration-[#62929e]/45 underline-offset-4 hover:text-[#4f7d87] dark:text-[#88d6e4] dark:hover:text-[#b8ebf3]"
                  >
                    Cookie Policy
                  </Link>
                  {" · "}
                  <Link
                    href="/api/v1/gdpr/privacy-policy"
                    target="_blank"
                    className="text-[#62929e] underline decoration-[#62929e]/45 underline-offset-4 hover:text-[#4f7d87] dark:text-[#88d6e4] dark:hover:text-[#b8ebf3]"
                  >
                    Privacy Policy
                  </Link>
                </p>
              </div>
            </div>

            <div className="grid w-full flex-shrink-0 grid-cols-1 gap-2 sm:grid-cols-3 lg:w-auto lg:min-w-[24rem]">
              <Button
                variant="outline"
                onClick={handleRejectNonEssential}
                className="h-10 border-[#546a7b]/35 bg-transparent text-sm text-[#393d3f] hover:border-[#546a7b]/55 hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/30 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
              >
                Reject Non-Essential
              </Button>

              <Link href="/cookie-preferences">
                <Button
                  variant="outline"
                  className="h-10 w-full border-[#546a7b]/35 bg-transparent text-sm text-[#393d3f] hover:border-[#546a7b]/55 hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/30 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                >
                  Customize
                </Button>
              </Link>

              <Button
                onClick={handleAcceptAll}
                className="h-10 bg-[#62929e] text-sm text-[#fdfdff] hover:bg-[#4f7d87]"
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
