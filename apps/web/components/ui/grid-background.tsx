export function GridBackground() {
  return (
    <div className="fixed inset-0 z-[-1] pointer-events-none">
      {/* Radial Gradient Fade */}
      <div className="absolute inset-0 bg-[#fdfdff] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px]" />

      {/* Floating Orbs for "Atmosphere" */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#62929e]/10 rounded-full blur-[128px]" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#c6c5b9]/40 rounded-full blur-[128px]" />
    </div>
  );
}
