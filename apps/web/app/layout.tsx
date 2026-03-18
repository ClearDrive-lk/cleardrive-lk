import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Libre_Baskerville } from "next/font/google";
import FloatingChatbot from "@/components/chat/FloatingChatbot";
import AppBackdrop from "@/components/ui/app-backdrop";
import ThemeInitScript from "@/components/ui/theme-init-script";
import "./globals.css";
import StoreProvider from "@/lib/store/StoreProvider";
import CookieBanner from "@/components/cookie/cookieBanner";
import { Toaster } from "@/components/ui/toaster";
import { ToastStateProvider } from "@/lib/hooks/use-toast";
import AuthBootstrap from "@/components/auth/AuthBootstrap";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

const libreBaskerville = Libre_Baskerville({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ClearDrive.lk",
  description: "Direct-access vehicle import terminal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${plusJakarta.variable} ${libreBaskerville.variable} font-sans antialiased bg-background text-foreground theme-override`}
      >
        <ThemeInitScript />
        <StoreProvider>
          <ToastStateProvider>
            <AuthBootstrap />
            <AppBackdrop />
            {children}
            <FloatingChatbot />
            <Toaster />
          </ToastStateProvider>
        </StoreProvider>
        <CookieBanner />
      </body>
    </html>
  );
}

