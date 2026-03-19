export const metadata = {
  title: "Terms of Service - ClearDrive.lk",
  description: "ClearDrive.lk terms of service and platform usage policy.",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#fdfdff] text-[#393d3f] py-16">
      <div className="cd-container space-y-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[#546a7b] font-mono">
            Legal
          </p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            Terms of Service
          </h1>
        </div>
        <p className="text-[#546a7b] leading-relaxed">
          These terms outline how ClearDrive.lk provides access to vehicle
          listings, bidding workflows, and clearance tools. By using the
          platform, you agree to comply with Sri Lankan import regulations,
          auction house rules, and payment requirements communicated during your
          order journey.
        </p>
        <ul className="space-y-3 text-sm text-[#546a7b]">
          <li>
            Accounts must be registered with accurate identity and contact
            details.
          </li>
          <li>
            Orders are only processed after deposits and applicable fees are
            confirmed.
          </li>
          <li>
            Live auction data is provided for informational use and may change
            without notice.
          </li>
          <li>
            Import duties, taxes, and clearance timelines are estimates and can
            shift due to regulatory updates.
          </li>
        </ul>
        <p className="text-sm text-[#546a7b]">
          For questions about these terms, contact{" "}
          <a
            href="mailto:support@cleardrive.lk"
            className="text-[#62929e] hover:text-[#62929e]/80"
          >
            support@cleardrive.lk
          </a>
          .
        </p>
      </div>
    </main>
  );
}
