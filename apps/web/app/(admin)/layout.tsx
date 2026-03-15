import { ReactNode } from "react";
import { AdminMobileNav, AdminSidebar } from "@/components/admin/AdminNav";
import AdminAccessGate from "@/components/admin/AdminAccessGate";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminAccessGate>
      <div className="admin-theme min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans relative">
        <div className="relative flex min-h-screen">
          <AdminSidebar />

          <div className="flex flex-1 flex-col">
            <header className="sticky top-0 z-30 flex items-center justify-between border-b border-white/10 bg-[#050505]/80 px-4 py-3 backdrop-blur lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#FE7743]/10 border border-[#FE7743]/30 text-sm font-semibold text-[#FE7743] shadow-lg shadow-orange-500/30">
                  CD
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-[0.4em] text-gray-500">
                    Admin
                  </p>
                  <p className="text-sm font-semibold text-white">
                    Control Room
                  </p>
                </div>
              </div>
              <AdminMobileNav />
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
