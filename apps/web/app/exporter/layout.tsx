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
        <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans relative flex flex-col">
          <ExporterNav />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
          <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />
          <main className="relative z-10 flex-1">{children}</main>
        </div>
      </ExporterAccessGate>
    </AuthGuard>
  );
}
