import type { Metadata } from "next";
import FloatingChatbot from "@/components/chat/FloatingChatbot";
import "./globals.css";
import StoreProvider from "@/lib/store/StoreProvider";
import CookieBanner from "@/components/cookie/cookieBanner";
import { Toaster } from "@/components/ui/toaster";
import { ToastStateProvider } from "@/lib/hooks/use-toast";
import AuthBootstrap from "@/components/auth/AuthBootstrap";

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
    <html lang="en">
      <body className="font-sans antialiased bg-[#050505]">
        <StoreProvider>
          <ToastStateProvider>
            <AuthBootstrap />
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
