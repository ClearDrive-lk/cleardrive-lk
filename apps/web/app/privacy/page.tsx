export const metadata = {
  title: "Privacy Policy - ClearDrive.lk",
  description: "How ClearDrive.lk collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#fdfdff] text-[#393d3f] py-16">
      <div className="cd-container space-y-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[#546a7b] font-mono">
            Legal
          </p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            Privacy Policy
          </h1>
        </div>
        <p className="text-[#546a7b] leading-relaxed">
          ClearDrive.lk collects the minimum data required to verify identity,
          process orders, and provide shipment updates. We use secure storage
          and encryption for sensitive records and never sell your personal
          information.
        </p>
        <ul className="space-y-3 text-sm text-[#546a7b]">
          <li>
            We store contact, identity, and transaction details to comply with
            KYC and import regulations.
          </li>
          <li>
            Payment references are stored for auditability and dispute
            resolution.
          </li>
          <li>
            Cookie preferences can be updated anytime from the footer links.
          </li>
        </ul>
        <p className="text-sm text-[#546a7b]">
          If you have questions about data handling, email{" "}
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
