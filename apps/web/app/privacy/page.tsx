import Header from "@/components/layout/Header";

export const metadata = {
  title: "Privacy Policy - ClearDrive.lk",
  description: "How ClearDrive.lk collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-[#fdfdff] py-16 text-[#393d3f] dark:bg-[#0f1417] dark:text-[#edf2f7]">
        <div className="cd-container space-y-6">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.3em] text-[#546a7b] dark:text-[#b8c7d4]">
              Legal
            </p>
            <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
              Privacy Policy
            </h1>
          </div>
          <p className="leading-relaxed text-[#546a7b] dark:text-[#bdcad4]">
            ClearDrive.lk collects the minimum data required to verify
            identity, process orders, and provide shipment updates. We use
            secure storage and encryption for sensitive records and never sell
            your personal information.
          </p>
          <ul className="space-y-3 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            <li>
              We store contact, identity, and transaction details to comply
              with KYC and import regulations.
            </li>
            <li>
              Payment references are stored for auditability and dispute
              resolution.
            </li>
            <li>
              Cookie preferences can be updated anytime from the footer links.
            </li>
          </ul>
          <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
            If you have questions about data handling, email{" "}
            <a
              href="mailto:support@cleardrive.lk"
              className="text-[#62929e] transition hover:text-[#62929e]/80 dark:text-[#88d6e4] dark:hover:text-[#9fe7f3]"
            >
              support@cleardrive.lk
            </a>
            .
          </p>
        </div>
      </main>
    </>
  );
}
