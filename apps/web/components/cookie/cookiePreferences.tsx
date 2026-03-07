"use client";

/**
 * Cookie preferences page - lets users update choices anytime.
 *
 * Author: Kalidu
 * Story: CD-101.5 - Cookie Preferences Page
 */

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import * as SwitchPrimitive from "@radix-ui/react-switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
  const [consent, setConsent] = useState<CookieConsent>(DEFAULT_CONSENT);
  const [saved, setSaved] = useState(false);

  // Load existing consent on mount
  useEffect(() => {
    const stored = getStoredConsent();
    if (stored) {
      setConsent(stored);
    }
  }, []);

  // Handle individual toggle
  const handleToggle = (
    key: keyof Omit<CookieConsent, "timestamp" | "version">,
  ) => {
    if (key === "essential") return; // Cannot toggle essential
    setConsent((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaved(false);
  };

  // Handle accept all
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

  // Handle reject non-essential
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

  // Handle save current selections
  const handleSave = () => {
    saveConsent(consent);
    showSavedMessage();
  };

  const showSavedMessage = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* ── Page Header ── */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cookie Preferences</h1>
        <p className="mt-2 text-gray-600">
          Control which cookies ClearDrive.lk uses. Essential cookies are always
          active. You can change your preferences at any time.
        </p>
      </div>

      {/* ── Category Cards ── */}
      <div className="space-y-4">
        {COOKIE_CATEGORIES.map((category) => (
          <div
            key={category.key}
            className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              {/* Left: Category info */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Label
                    htmlFor={`switch-${category.key}`}
                    className="text-base font-semibold text-gray-900 cursor-pointer"
                  >
                    {category.label}
                  </Label>

                  {category.alwaysOn && (
                    <Badge variant="secondary" className="text-xs">
                      Always Active
                    </Badge>
                  )}
                </div>

                <p className="text-sm text-gray-600 mb-2">
                  {category.description}
                </p>

                {/* Examples */}
                <div className="flex flex-wrap gap-1.5">
                  {category.examples.map((example) => (
                    <span
                      key={example}
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
                    >
                      {example}
                    </span>
                  ))}
                </div>
              </div>

              {/* Right: Toggle */}
              <div className="flex-shrink-0 mt-1">
                <SwitchPrimitive.Root
                  id={`switch-${category.key}`}
                  checked={consent[category.key] as boolean}
                  onCheckedChange={() => handleToggle(category.key)}
                  disabled={category.alwaysOn}
                  aria-label={`Toggle ${category.label}`}
                  className="w-11 h-6 bg-gray-300 rounded-full relative data-[state=checked]:bg-blue-600 cursor-pointer"
                >
                  <SwitchPrimitive.Thumb className="w-5 h-5 bg-white rounded-full shadow-sm absolute top-0.5 left-0.5 data-[state=checked]:translate-x-5 transition-transform" />
                </SwitchPrimitive.Root>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Action Buttons ── */}
      <div className="mt-8 flex flex-col sm:flex-row gap-3">
        <Button variant="outline" onClick={handleRejectAll} className="flex-1">
          Reject Non-Essential
        </Button>

        <Button variant="outline" onClick={handleAcceptAll} className="flex-1">
          Accept All
        </Button>

        <Button
          onClick={handleSave}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
        >
          {saved ? "✅ Saved!" : "Save Preferences"}
        </Button>
      </div>

      {/* ── Success message ── */}
      {saved && (
        <p className="mt-4 text-sm text-green-600 text-center font-medium">
          Your preferences have been saved successfully.
        </p>
      )}

      {/* ── Policy Links ── */}
      <p className="mt-6 text-xs text-gray-500 text-center">
        Learn more in our{" "}
        <a
          href="/api/v1/gdpr/cookie-policy"
          target="_blank"
          className="text-blue-600 underline"
        >
          Cookie Policy
        </a>
        {" · "}
        <a
          href="/api/v1/gdpr/privacy-policy"
          target="_blank"
          className="text-blue-600 underline"
        >
          Privacy Policy
        </a>
      </p>
    </div>
  );
}
