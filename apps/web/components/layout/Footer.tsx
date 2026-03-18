import Link from "next/link";
import { Terminal, ArrowRight } from "lucide-react";

/**
 * Footer Component - Matching homepage design
 */
export default function Footer() {
  return (
    <footer className="border-t border-[#546a7b]/65 py-16 bg-[#fdfdff]">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
        {/* Company Info */}
        <div className="space-y-6">
          <div className="font-bold text-xl tracking-tighter text-[#393d3f] flex items-center gap-2">
            <Terminal className="w-5 h-5 text-[#62929e]" />
            ClearDrive<span className="text-[#62929e]">.lk</span>
          </div>
          <p className="text-sm text-[#546a7b] leading-relaxed">
            The first tech-enabled vehicle import platform in Sri Lanka.
            Replacing brokers with code, ensuring 100% financial transparency.
          </p>
        </div>

        {/* Market Data */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Market Data</h4>
          <ul className="space-y-3 text-sm text-[#546a7b] font-mono">
            <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
              <ArrowRight className="w-3 h-3" /> USS Tokyo Live
            </li>
            <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
              <ArrowRight className="w-3 h-3" /> JAA Condition Sheets
            </li>
            <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
              <ArrowRight className="w-3 h-3" /> Cost Calculator
            </li>
            <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
              <ArrowRight className="w-3 h-3" /> Past Sales (2025)
            </li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Company</h4>
          <ul className="space-y-3 text-sm text-[#546a7b]">
            <li className="hover:text-[#62929e] cursor-pointer">About Us</li>
            <li className="hover:text-[#62929e] cursor-pointer">Careers</li>
            <li className="hover:text-[#62929e] cursor-pointer">
              Terms of Service
            </li>
            <li className="hover:text-[#62929e] cursor-pointer">
              Privacy Policy
            </li>
          </ul>
        </div>

        {/* Support */}
        <div>
          <h4 className="font-bold text-[#393d3f] mb-6">Support</h4>
          <ul className="space-y-3 text-sm text-[#546a7b]">
            <li className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500" /> Systems
              Operational
            </li>
            <li>Colombo 03, Sri Lanka</li>
            <li>support@cleardrive.lk</li>
            <li>+94 77 123 4567</li>
          </ul>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-[#546a7b]/40 flex flex-col md:flex-row justify-between items-center text-xs text-[#393d3f] font-mono">
        <p>© 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
        <p>DESIGNED FOR HIGH-FREQUENCY TRADING</p>
      </div>

      {/*cookie banner*/}
      <nav aria-label="Legal links">
        <Link
          href="/cookie-preferences"
          className="text-sm text-[#546a7b] hover:text-gray-700"
        >
          Cookie Preferences
        </Link>
        <Link
          href="http://localhost:8000/api/v1/gdpr/privacy-policy"
          target="_blank"
          className="text-sm text-[#546a7b] hover:text-gray-700"
        >
          Privacy Policy
        </Link>
        <Link
          href="http://localhost:8000/api/v1/gdpr/cookie-policy"
          target="_blank"
          className="text-sm text-[#546a7b] hover:text-gray-700"
        >
          Cookie Policy
        </Link>
      </nav>
    </footer>
  );
}

