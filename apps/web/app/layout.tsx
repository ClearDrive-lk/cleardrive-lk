import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import StoreProvider from "@/lib/store/StoreProvider";

// Define the font
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
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
    <html lang="en">
      {/* Apply the font variable */}
      <body className={`${inter.variable} font-sans antialiased bg-[#050505]`}>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
