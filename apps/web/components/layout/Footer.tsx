import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { BrandMark, BrandWordmark } from "@/components/ui/brand";

/**
 * Footer Component - Matching homepage design
 */
export default function Footer() {
  return (
    <footer className="border-t border-[#546a7b]/65 py-16 bg-[#fdfdff]">
      <div className="cd-container grid grid-cols-1 md:grid-cols-4 gap-12">
        {/* Company Info */}
        <div className="space-y-6">
          <div className="font-bold text-xl tracking-tighter text-[#393d3f] flex items-center gap-2">
            <BrandMark className="h-8 w-8 rounded-md border border-[#62929e]/20 bg-[#62929e]/10" />
            <BrandWordmark />
          </div>
          <p className="text-sm text-[#546a7b] leading-relaxed">
            The first tech-enabled vehicle import platform in Sri Lanka.
            Replacing brokers with code, ensuring 100% financial transparency.
          </p>
          <div className="flex flex-wrap gap-3 text-[11px] text-[#546a7b] font-mono uppercase tracking-[0.2em]">
            <span>Colombo HQ</span>
            <span>Mon-Sat 9am-6pm</span>
          </div>
        </div>

        {/* Platform */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Platform</h4>
          <ul className="space-y-3 text-sm text-[#546a7b] font-mono">
            <li>
              <Link
                href="/dashboard"
                className="hover:text-[#62929e] flex items-center gap-2"
              >
                <ArrowRight className="w-3 h-3" /> Dashboard
              </Link>
            </li>
            <li>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#62929e] flex items-center gap-2"
              >
                <ArrowRight className="w-3 h-3" /> Live Auctions
              </Link>
            </li>
            <li>
              <Link
                href="/dashboard/orders"
                className="hover:text-[#62929e] flex items-center gap-2"
              >
                <ArrowRight className="w-3 h-3" /> Orders & Tracking
              </Link>
            </li>
            <li>
              <Link
                href="/exporter"
                className="hover:text-[#62929e] flex items-center gap-2"
              >
                <ArrowRight className="w-3 h-3" /> Exporter Terminal
              </Link>
            </li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Company</h4>
          <ul className="space-y-3 text-sm text-[#546a7b]">
            <li>
              <Link href="/about" className="hover:text-[#62929e]">
                About Us
              </Link>
            </li>
            <li>
              <Link href="/about#careers" className="hover:text-[#62929e]">
                Careers
              </Link>
            </li>
            <li>
              <Link href="/terms" className="hover:text-[#62929e]">
                Terms of Service
              </Link>
            </li>
            <li>
              <Link href="/privacy" className="hover:text-[#62929e]">
                Privacy Policy
              </Link>
            </li>
          </ul>
        </div>

        {/* Support */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Support</h4>
          <ul className="space-y-3 text-sm text-[#546a7b]">
            <li>
              <Link
                href="/dashboard"
                className="flex items-center gap-2 hover:text-[#62929e]"
              >
                <span className="w-2 h-2 rounded-full bg-green-500" />
                System Status
              </Link>
            </li>
            <li>
              <a
                href="mailto:support@cleardrive.lk"
                className="hover:text-[#62929e]"
              >
                support@cleardrive.lk
              </a>
            </li>
            <li>
              <a href="tel:+94771234567" className="hover:text-[#62929e]">
                +94 77 123 4567
              </a>
            </li>
            <li>
              <a
                href="https://maps.google.com/?q=Colombo%2003%2C%20Sri%20Lanka"
                target="_blank"
                rel="noreferrer"
                className="hover:text-[#62929e]"
              >
                Colombo 03, Sri Lanka
              </a>
            </li>
            <li>
              <Link href="/cookie-preferences" className="hover:text-[#62929e]">
                Cookie Preferences
              </Link>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="cd-container mt-16 pt-8 border-t border-[#546a7b]/40 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-[#393d3f] font-mono">
        <p>(c) 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
        <nav
          aria-label="Legal links"
          className="flex flex-wrap items-center gap-4 text-xs text-[#546a7b]"
        >
          <Link href="/terms" className="hover:text-[#62929e]">
            Terms
          </Link>
          <Link href="/privacy" className="hover:text-[#62929e]">
            Privacy
          </Link>
          <Link href="/cookie-preferences" className="hover:text-[#62929e]">
            Cookies
          </Link>
        </nav>
      </div>
    </footer>
  );
}
