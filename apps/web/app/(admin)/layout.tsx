import { ReactNode } from "react";
import { AdminMobileNav, AdminSidebar } from "@/components/admin/AdminNav";
import AdminLogoutButton from "@/components/admin/AdminLogoutButton";
import ThemeToggle from "@/components/ui/theme-toggle";
import AdminAccessGate from "@/components/admin/AdminAccessGate";
import { BrandMark } from "@/components/ui/brand";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminAccessGate>
      <div className="admin-theme relative min-h-screen font-sans text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff]">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(95%_70%_at_0%_0%,color-mix(in_oklab,hsl(var(--primary))_16%,transparent),transparent_55%),radial-gradient(70%_60%_at_100%_0%,color-mix(in_oklab,hsl(var(--secondary))_18%,transparent),transparent_58%)]" />
        <div className="relative flex min-h-screen">
          <AdminSidebar />

          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-30 border-b border-[#546a7b]/65 bg-[#fdfdff]/80 py-3 backdrop-blur-xl">
              <div className="cd-container flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BrandMark className="h-10 w-10 rounded-2xl border border-[#62929e]/30 bg-[#62929e]/10 p-2 shadow-lg shadow-[0_0_20px_rgba(98,146,158,0.3)]" />
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.4em] text-[#546a7b]">
                      Admin
                    </p>
                    <p className="text-sm font-semibold text-[#393d3f]">
                      Control Room
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-right md:block">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-[#546a7b]">
                      Operations
                    </p>
                    <p className="text-xs font-semibold text-[#393d3f]">
                      Live monitoring enabled
                    </p>
                  </div>
                  <AdminLogoutButton />
                  <ThemeToggle />
                  <div className="lg:hidden">
                    <AdminMobileNav />
                  </div>
                </div>
              </div>
            </header>

            <main className="relative flex-1 overflow-y-auto">
              <div className="relative">{children}</div>
            </main>
          </div>
        </div>
      </div>
    </AdminAccessGate>
  );
}
