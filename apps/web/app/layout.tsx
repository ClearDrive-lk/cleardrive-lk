import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ClearDrive.lk",
  description: "Premium Vehicle Import Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      {/* We force the background color here with bg-[#050505] to prevent white flashes */}
      <body className={`${inter.className} min-h-screen bg-[#050505] text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}