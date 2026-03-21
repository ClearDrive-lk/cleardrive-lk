// frontend/app/cookie-preferences/page.tsx

import CookiePreferences from "@/components/cookie/cookiePreferences";
import Header from "@/components/layout/Header";

export const metadata = {
  title: "Cookie Preferences - ClearDrive.lk",
  description: "Manage your cookie preferences for ClearDrive.lk",
};

export default function CookiePreferencesPage() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-gray-50 py-10 dark:bg-[#0f1417]">
        <CookiePreferences />
      </main>
    </>
  );
}
