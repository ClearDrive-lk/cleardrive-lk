// frontend/app/cookie-preferences/page.tsx

import CookiePreferences from "@/components/cookie/cookiePreferences";

export const metadata = {
  title: "Cookie Preferences - ClearDrive.lk",
  description: "Manage your cookie preferences for ClearDrive.lk",
};

export default function CookiePreferencesPage() {
  return (
    <main className="min-h-screen bg-gray-50 py-10">
      <CookiePreferences />
    </main>
  );
}
