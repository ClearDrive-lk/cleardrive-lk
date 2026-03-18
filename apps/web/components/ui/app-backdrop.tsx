export default function AppBackdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10" aria-hidden="true">
      <div
        className="absolute inset-0 app-backdrop__main"
        style={{ backgroundImage: "var(--app-backdrop-main)" }}
      />
      <div
        className="absolute inset-0 app-backdrop__orbits"
        style={{ backgroundImage: "var(--app-backdrop-orbits)" }}
      />
      <div
        className="absolute inset-0 opacity-45 mix-blend-multiply"
        style={{
          backgroundImage: "var(--app-backdrop-grid)",
          backgroundSize: "64px 64px",
        }}
      />
      <div
        className="absolute inset-0 opacity-28"
        style={{ backgroundImage: "var(--app-backdrop-diagonal)" }}
      />
      <div
        className="absolute -top-24 left-1/2 h-64 w-[80vw] -translate-x-1/2 rounded-full app-backdrop__glow blur-[26px]"
        style={{ backgroundImage: "var(--app-backdrop-glow)" }}
      />
      <div
        className="absolute inset-0"
        style={{ backgroundImage: "var(--app-backdrop-vignette)" }}
      />
    </div>
  );
}
