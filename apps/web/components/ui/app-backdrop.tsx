export default function AppBackdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10">
      <div className="absolute inset-0 bg-[radial-gradient(1200px_600px_at_12%_-10%,rgba(98,146,158,0.26),transparent_60%),radial-gradient(900px_520px_at_88%_0%,rgba(84,106,123,0.24),transparent_55%),linear-gradient(180deg,#a49a90_0%,#9b9188_52%,#91877f_100%)]" />
      <div className="absolute inset-0 opacity-8 bg-[radial-gradient(circle_at_18%_20%,rgba(98,146,158,0.22),transparent_52%),radial-gradient(circle_at_82%_25%,rgba(84,106,123,0.2),transparent_58%)]" />
      <div className="absolute inset-0 opacity-45 mix-blend-multiply bg-[linear-gradient(to_right,rgba(57,61,63,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(57,61,63,0.12)_1px,transparent_1px)] bg-[size:64px_64px]" />
      <div className="absolute inset-0 opacity-28 bg-[repeating-linear-gradient(115deg,rgba(57,61,63,0.08)_0,rgba(57,61,63,0.08)_2px,transparent_2px,transparent_26px)]" />
      <div className="absolute -top-24 left-1/2 h-64 w-[80vw] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(198,197,185,0.28),transparent_70%)] blur-[26px]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_110%,rgba(0,0,0,0.28),transparent_60%)]" />
    </div>
  );
}
