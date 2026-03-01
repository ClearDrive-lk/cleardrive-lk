/**
 * Cookie consent types.
 * Author: Kalidu
 * Story: CD-101 - Cookie Consent Banner
 */

export interface CookieConsent {
  essential: boolean; // Always true - cannot be disabled
  functional: boolean; // Language, theme preferences
  analytics: boolean; // Google Analytics
  marketing: boolean; // Facebook Pixel, Google Ads
  timestamp: string; // When consent was given
  version: string; // Policy version number
}

export type CookieCategory = keyof Omit<CookieConsent, "timestamp" | "version">;

export const DEFAULT_CONSENT: CookieConsent = {
  essential: true, // Always on
  functional: false,
  analytics: false,
  marketing: false,
  timestamp: "",
  version: "1.0",
};

export const FULL_CONSENT: CookieConsent = {
  essential: true,
  functional: true,
  analytics: true,
  marketing: true,
  timestamp: new Date().toISOString(),
  version: "1.0",
};

export const COOKIE_CONSENT_KEY = "cleardrive_cookie_consent";
