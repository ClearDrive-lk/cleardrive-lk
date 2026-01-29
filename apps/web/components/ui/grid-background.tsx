export function GridBackground() {
    return (
      <div className="fixed inset-0 z-[-1] pointer-events-none">
        {/* Radial Gradient Fade */}
        <div className="absolute inset-0 bg-[#050505] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        
        {/* Floating Orbs for "Atmosphere" */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#FE7743]/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#273F4F]/20 rounded-full blur-[128px]" />
      </div>
    );
  }