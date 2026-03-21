"use client";

/**
 * Cookie preferences page - lets users update choices anytime.
 *
 * Author: Kalidu
 * Story: CD-101.5 - Cookie Preferences Page
 */

import { useState } from "react";
import * as SwitchPrimitive from "@radix-ui/react-switch";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { getStoredConsent, saveConsent } from "@/lib/cookies/utils";
import { CookieConsent, DEFAULT_CONSENT } from "@/lib/cookies/types";

interface CookieCategory {
  key: keyof Omit<CookieConsent, "timestamp" | "version">;
  label: string;
  description: string;
  examples: string[];
  alwaysOn: boolean;
}

const COOKIE_CATEGORIES: CookieCategory[] = [
  {
    key: "essential",
    label: "Essential Cookies",
    description:
      "These cookies are necessary for the website to work. They cannot be disabled.",
    examples: ["Login session", "Security tokens", "Load balancing"],
    alwaysOn: true,
  },
  {
    key: "functional",
    label: "Functional Cookies",
    description:
      "These cookies remember your preferences and settings to enhance your experience.",
    examples: ["Language preference", "Dark/light mode", "Currency display"],
    alwaysOn: false,
  },
  {
    key: "analytics",
    label: "Analytics Cookies",
    description:
      "These cookies help us understand how you use our site so we can improve it.",
    examples: ["Google Analytics", "Page views", "User behaviour"],
    alwaysOn: false,
  },
  {
    key: "marketing",
    label: "Marketing Cookies",
    description:
      "These cookies are used to show you relevant advertisements on other websites.",
    examples: ["Facebook Pixel", "Google Ads", "Retargeting"],
    alwaysOn: false,
  },
];

export default function CookiePreferences() {
  const [consent, setConsent] = useState<CookieConsent>(
    () => getStoredConsent() ?? DEFAULT_CONSENT,
  );
  const [saved, setSaved] = useState(false);

  const handleToggle = (
    key: keyof Omit<CookieConsent, "timestamp" | "version">,
  ) => {
    if (key === "essential") return;
    setConsent((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaved(false);
  };

  const handleAcceptAll = () => {
    const fullConsent: CookieConsent = {
      essential: true,
      functional: true,
      analytics: true,
      marketing: true,
      timestamp: new Date().toISOString(),
      version: "1.0",
    };
    setConsent(fullConsent);
    saveConsent(fullConsent);
    showSavedMessage();
  };

  const handleRejectAll = () => {
    const minConsent: CookieConsent = {
      ...DEFAULT_CONSENT,
      essential: true,
      timestamp: new Date().toISOString(),
      version: "1.0",
    };
    setConsent(minConsent);
    saveConsent(minConsent);
    showSavedMessage();
  };

  const handleSave = () => {
    saveConsent(consent);
    showSavedMessage();
  };

  const showSavedMessage = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#393d3f] dark:text-[#edf2f7]">
          Cookie Preferences
        </h1>
        <p className="mt-2 text-[#546a7b] dark:text-[#bdcad4]">
          Control which cookies ClearDrive.lk uses. Essential cookies are always
          active. You can change your preferences at any time.
        </p>
      </div>

      <div className="space-y-4">
        {COOKIE_CATEGORIES.map((category) => (
          <div
            key={category.key}
            className="rounded-xl border border-gray-200 bg-[#fdfdff] p-5 shadow-sm dark:border-[#355061] dark:bg-[#131c21]"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Label
                    htmlFor={`switch-${category.key}`}
                    className="cursor-pointer text-base font-semibold text-[#393d3f] dark:text-[#edf2f7]"
                  >
                    {category.label}
                  </Label>

                  {category.alwaysOn && (
                    <Badge variant="secondary" className="text-xs">
                      Always Active
                    </Badge>
                  )}
                </div>

                <p className="mb-2 text-sm text-[#546a7b] dark:text-[#bdcad4]">
                  {category.description}
                </p>

                <div className="flex flex-wrap gap-1.5">
                  {category.examples.map((example) => (
                    <span
                      key={example}
                      className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-[#393d3f] dark:bg-[#22313c] dark:text-[#d6e2eb]"
                    >
                      {example}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-1 flex-shrink-0">
                <SwitchPrimitive.Root
                  id={`switch-${category.key}`}
                  checked={consent[category.key] as boolean}
                  onCheckedChange={() => handleToggle(category.key)}
                  disabled={category.alwaysOn}
                  aria-label={`Toggle ${category.label}`}
                  className="relative h-6 w-11 cursor-pointer rounded-full bg-gray-300 data-[state=checked]:bg-[#62929e] dark:bg-[#304757] dark:data-[state=checked]:bg-[#88d6e4]"
                >
                  <SwitchPrimitive.Thumb className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-[#fdfdff] shadow-sm transition-transform data-[state=checked]:translate-x-5 dark:bg-[#0f1417]" />
                </SwitchPrimitive.Root>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Button
          variant="outline"
          onClick={handleRejectAll}
          className="flex-1 border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
        >
          Reject Non-Essential
        </Button>

        <Button
          variant="outline"
          onClick={handleAcceptAll}
          className="flex-1 border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
        >
          Accept All
        </Button>

        <Button
          onClick={handleSave}
          className="flex-1 bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 dark:bg-[#88d6e4] dark:text-[#0f1417] dark:hover:bg-[#9fe7f3]"
        >
          {saved ? "Saved!" : "Save Preferences"}
        </Button>
      </div>

      {saved && (
        <p className="mt-4 text-center text-sm font-medium text-green-700 dark:text-green-300">
          Your preferences have been saved successfully.
        </p>
      )}

      <p className="mt-6 text-center text-xs text-[#546a7b] dark:text-[#bdcad4]">
        Learn more in our{" "}
        <a
          href="/api/v1/gdpr/cookie-policy"
          target="_blank"
          rel="noreferrer"
          className="text-[#62929e] underline transition hover:text-[#62929e]/80 dark:text-[#88d6e4] dark:hover:text-[#9fe7f3]"
        >
          Cookie Policy
        </a>
        {" | "}
        <a
          href="/api/v1/gdpr/privacy-policy"
          target="_blank"
          rel="noreferrer"
          className="text-[#62929e] underline transition hover:text-[#62929e]/80 dark:text-[#88d6e4] dark:hover:text-[#9fe7f3]"
        >
          Privacy Policy
        </a>
      </p>
    </div>
  );
}
