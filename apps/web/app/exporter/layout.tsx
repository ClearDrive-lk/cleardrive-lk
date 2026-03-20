import AuthGuard from "@/components/auth/AuthGuard";
import ExporterAccessGate from "@/components/exporter/ExporterAccessGate";
import ExporterNav from "@/components/exporter/ExporterNav";

export default function ExporterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <ExporterAccessGate>
        <div className="relative flex min-h-screen flex-col bg-[#fdfdff] font-sans text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] dark:bg-[#0f1417] dark:text-[#edf2f7]">
          <ExporterNav />
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(198,197,185,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(198,197,185,0.1)_1px,transparent_1px)] bg-[size:42px_42px] dark:bg-[linear-gradient(to_right,rgba(143,163,177,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(143,163,177,0.08)_1px,transparent_1px)]" />
          <div className="pointer-events-none absolute left-1/2 top-[5%] h-[620px] w-[1000px] -translate-x-1/2 rounded-[100%] bg-[#62929e]/8 blur-[120px] dark:bg-[#88d6e4]/12" />
          <main className="relative z-10 flex-1">{children}</main>
        </div>
      </ExporterAccessGate>
    </AuthGuard>
  );
}
