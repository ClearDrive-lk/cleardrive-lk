import { ReactNode } from "react";
import { AdminMobileNav, AdminSidebar } from "@/components/admin/AdminNav";
import ThemeToggle from "@/components/ui/theme-toggle";
import AdminAccessGate from "@/components/admin/AdminAccessGate";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminAccessGate>
      <div className="admin-theme min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans relative">
        <div className="relative flex min-h-screen">
          <AdminSidebar />

          <div className="flex flex-1 flex-col">
            <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[#546a7b]/65 bg-[#fdfdff]/80 px-4 py-3 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#62929e]/10 border border-[#62929e]/30 text-sm font-semibold text-[#62929e] shadow-lg shadow-[0_0_20px_rgba(98,146,158,0.3)]">
                  CD
                </div>
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
                <ThemeToggle />
                <div className="lg:hidden">
                  <AdminMobileNav />
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
