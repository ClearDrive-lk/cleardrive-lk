/**
 * Cookie consent utility functions.
 * Author: Kalidu
 * Story: CD-101
 */

import { CookieConsent, DEFAULT_CONSENT, COOKIE_CONSENT_KEY } from "./types";

/**
 * Get stored cookie consent from localStorage.
 * Returns null if no consent stored yet.
 */
export function getStoredConsent(): CookieConsent | null {
  // Guard against server-side rendering
  if (typeof window === "undefined") return null;

  try {
    const stored = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as CookieConsent;
  } catch {
    return null;
  }
}

/**
 * Save cookie consent to localStorage.
 */
export function saveConsent(consent: CookieConsent): void {
  if (typeof window === "undefined") return;

  const consentWithTimestamp: CookieConsent = {
    ...consent,
    essential: true, // Always force essential=true
    timestamp: new Date().toISOString(),
    version: "1.0",
  };

  localStorage.setItem(
    COOKIE_CONSENT_KEY,
    JSON.stringify(consentWithTimestamp),
  );

  // Notify mounted components (e.g., banner) that consent changed.
  window.dispatchEvent(new Event("cleardrive:cookie-consent-updated"));
}

/**
 * Check if user has already given consent (any choice).
 */
export function hasConsented(): boolean {
  return getStoredConsent() !== null;
}

/**
 * Check if a specific category is accepted.
 */
export function isCategoryAccepted(category: keyof CookieConsent): boolean {
  const consent = getStoredConsent();
  if (!consent) return false;
  return consent[category] === true;
}

/**
 * Accept all cookies.
 */
export function acceptAll(): void {
  saveConsent({
    essential: true,
    functional: true,
    analytics: true,
    marketing: true,
    timestamp: new Date().toISOString(),
    version: "1.0",
  });
}

/**
 * Reject non-essential cookies (keep only essential).
 */
export function rejectNonEssential(): void {
  saveConsent({
    ...DEFAULT_CONSENT,
    essential: true,
    timestamp: new Date().toISOString(),
    version: "1.0",
  });
}

/**
 * Clear all consent (e.g., when policy updates).
 */
export function clearConsent(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(COOKIE_CONSENT_KEY);
}
