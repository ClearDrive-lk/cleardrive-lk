"use client";

import Link from "next/link";
import { ShieldAlert, ArrowRight } from "lucide-react";
import { useAppSelector } from "@/lib/store/store";
import { Button } from "@/components/ui/button";
import { normalizeRole, roleHomePath } from "@/lib/roles";

export default function ExporterAccessGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  if (!isAuthenticated) {
    return null;
  }

  const role = normalizeRole(user?.role);
  const allowed = role === "EXPORTER" || role === "ADMIN";

  if (!allowed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#fdfdff] px-6 text-[#393d3f] dark:bg-[#0f1417] dark:text-[#edf2f7]">
        <div className="max-w-lg rounded-2xl border border-[#546a7b]/45 bg-[#fdfdff]/80 p-10 text-center dark:border-[#8fa3b1]/30 dark:bg-[#131d23]/75">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10 text-red-400">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-semibold text-[#393d3f] dark:text-[#edf2f7]">
            Exporter Access Required
          </h1>
          <p className="mt-3 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            Your account does not have access to the exporter terminal. If this
            is unexpected, contact an administrator for role approval.
          </p>
          <Button
            asChild
            className="mt-6 bg-[#62929e] text-[#fdfdff] font-semibold"
          >
            <Link href={roleHomePath(role)}>
              Return to your dashboard <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
