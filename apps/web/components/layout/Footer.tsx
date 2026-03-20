import Link from "next/link";
import {
  ArrowUpRight,
  CircleCheckBig,
  Clock3,
  Mail,
  MapPin,
  PhoneCall,
} from "lucide-react";

import { BrandMark, BrandWordmark } from "@/components/ui/brand";

const platformLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/vehicles", label: "Live Auctions" },
  { href: "/dashboard/orders", label: "Orders & Tracking" },
  { href: "/exporter", label: "Exporter Terminal" },
];

const companyLinks = [
  { href: "/about", label: "About Us" },
  { href: "/about#careers", label: "Careers" },
  { href: "/terms", label: "Terms of Service" },
  { href: "/privacy", label: "Privacy Policy" },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative w-full overflow-hidden border-t border-[#546a7b]/65 bg-[#fdfdff] pb-8 pt-14 dark:border-[#8fa3b1]/35 dark:bg-[#0f1417]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_12%,rgba(98,146,158,0.14),transparent_44%),radial-gradient(circle_at_88%_0%,rgba(84,106,123,0.18),transparent_35%)] dark:bg-[radial-gradient(circle_at_12%_12%,rgba(136,214,228,0.16),transparent_44%),radial-gradient(circle_at_88%_0%,rgba(98,146,158,0.22),transparent_35%)]" />

      <div className="relative z-10 w-full space-y-10 px-4 sm:px-6 md:px-10 xl:px-14">
        <section className="w-full rounded-3xl border border-white/20 bg-[linear-gradient(120deg,#0f2230,#132d3f_52%,#16384d)] p-5 text-white shadow-[0_20px_45px_rgba(6,18,28,0.4)] md:p-7">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <p className="text-[11px] font-mono uppercase tracking-[0.28em] text-white/70">
                Trusted Import Operations
              </p>
              <h3 className="text-xl font-semibold text-white md:text-2xl">
                Need help with your next vehicle import?
              </h3>
              <p className="max-w-2xl text-sm text-white/85">
                Our team supports importer onboarding, tax estimates, and
                end-to-end order tracking with full financial transparency.
              </p>
            </div>
            <a
              href="mailto:support@cleardrive.lk?subject=Start%20Vehicle%20Import%20Consultation"
              className="group inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/25 bg-white/12 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-white/20 md:w-auto"
            >
              Start Import Consultation
              <ArrowUpRight className="h-4 w-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          </div>
        </section>

        <div className="grid w-full grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-4">
          <section className="space-y-5">
            <div className="flex items-center gap-2 text-xl font-bold tracking-tight text-[#393d3f] dark:text-[#edf2f7]">
              <BrandMark className="h-9 w-9 rounded-md border border-[#62929e]/30 bg-[#62929e]/10" />
              <BrandWordmark />
            </div>
            <p className="text-sm leading-relaxed text-[#546a7b] dark:text-[#bdcad4]">
              Sri Lanka&apos;s direct-access vehicle import platform, replacing
              opaque broker workflows with fast, transparent digital operations.
            </p>
            <div className="space-y-2 text-xs text-[#546a7b] dark:text-[#bdcad4]">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 font-mono uppercase tracking-[0.2em] text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-500/12 dark:text-emerald-300">
                <CircleCheckBig className="h-3.5 w-3.5" />
                Live Platform Status
              </div>
              <div className="flex items-center gap-2 font-mono uppercase tracking-[0.14em]">
                <Clock3 className="h-3.5 w-3.5" />
                Mon-Sat 9:00 AM to 6:00 PM
              </div>
            </div>
          </section>

          <nav aria-label="Platform links">
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-[0.14em] text-[#393d3f] dark:text-[#edf2f7]">
              Platform
            </h4>
            <ul className="space-y-3 text-sm text-[#546a7b] dark:text-[#bdcad4]">
              {platformLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="group inline-flex items-center gap-2 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                  >
                    <ArrowUpRight className="h-3.5 w-3.5 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="Company links">
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-[0.14em] text-[#393d3f] dark:text-[#edf2f7]">
              Company
            </h4>
            <ul className="space-y-3 text-sm text-[#546a7b] dark:text-[#bdcad4]">
              {companyLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/cookie-preferences"
                  className="transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                >
                  Cookie Preferences
                </Link>
              </li>
            </ul>
          </nav>

          <section className="space-y-4 rounded-2xl border border-[#546a7b]/30 bg-[#fdfdff]/70 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.08)] dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75 dark:shadow-[0_14px_30px_rgba(0,0,0,0.28)]">
            <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#393d3f] dark:text-[#edf2f7]">
              Support
            </h4>
            <ul className="space-y-3 text-sm text-[#546a7b] dark:text-[#bdcad4]">
              <li>
                <a
                  href="mailto:support@cleardrive.lk"
                  className="inline-flex items-center gap-2 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                >
                  <Mail className="h-4 w-4" />
                  support@cleardrive.lk
                </a>
              </li>
              <li>
                <a
                  href="mailto:cleardrivelk@gmail.com"
                  className="inline-flex items-center gap-2 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                >
                  <Mail className="h-4 w-4" />
                  cleardrivelk@gmail.com
                </a>
              </li>
              <li>
                <a
                  href="tel:+94771234567"
                  className="inline-flex items-center gap-2 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                >
                  <PhoneCall className="h-4 w-4" />
                  +94 77 695 7571
                </a>
              </li>
              <li>
                <a
                  href="https://maps.google.com/?q=Colombo%2003%2C%20Sri%20Lanka"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
                >
                  <MapPin className="h-4 w-4" />
                  Colombo 03, Sri Lanka
                </a>
              </li>
            </ul>
          </section>
        </div>

        <div className="flex flex-col gap-4 border-t border-[#546a7b]/40 pt-6 text-xs text-[#546a7b] dark:border-[#8fa3b1]/35 dark:text-[#bdcad4] md:flex-row md:items-center md:justify-between">
          <p className="font-mono uppercase tracking-[0.18em] text-[#393d3f] dark:text-[#edf2f7]">
            (c) {year} CLEARDRIVE INC. ALL RIGHTS RESERVED.
          </p>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <Link
              href="/terms"
              className="transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
            >
              Terms
            </Link>
            <Link
              href="/privacy"
              className="transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
            >
              Privacy
            </Link>
            <Link
              href="/cookie-preferences"
              className="transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
            >
              Cookies
            </Link>
            <a
              href="#"
              className="inline-flex items-center gap-1.5 transition hover:text-[#62929e] dark:hover:text-[#88d6e4]"
            >
              Back to top
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
