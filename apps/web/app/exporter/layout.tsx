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
        <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans relative flex flex-col">
          <ExporterNav />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
          <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />
          <main className="relative z-10 flex-1">{children}</main>
        </div>
      </ExporterAccessGate>
    </AuthGuard>
  );
}

