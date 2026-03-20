const ORDER_STATUS_BADGE_CLASSES: Record<string, string> = {
  CREATED: "border-sky-500/30 bg-sky-500/15 text-sky-800 dark:text-sky-200",
  PAYMENT_CONFIRMED:
    "border-emerald-500/30 bg-emerald-500/15 text-emerald-800 dark:text-emerald-200",
  LC_REQUESTED:
    "border-amber-500/30 bg-amber-500/15 text-amber-800 dark:text-amber-200",
  LC_APPROVED:
    "border-emerald-500/30 bg-emerald-500/15 text-emerald-800 dark:text-emerald-200",
  LC_REJECTED: "border-red-500/30 bg-red-500/15 text-red-800 dark:text-red-200",
  ASSIGNED_TO_EXPORTER:
    "border-fuchsia-500/30 bg-fuchsia-500/15 text-fuchsia-800 dark:text-fuchsia-200",
  SHIPMENT_DOCS_UPLOADED:
    "border-violet-500/30 bg-violet-500/15 text-violet-800 dark:text-violet-200",
  AWAITING_SHIPMENT_CONFIRMATION:
    "border-orange-500/30 bg-orange-500/15 text-orange-800 dark:text-orange-200",
  SHIPPED:
    "border-indigo-500/30 bg-indigo-500/15 text-indigo-800 dark:text-indigo-200",
  IN_TRANSIT: "border-cyan-500/30 bg-cyan-500/15 text-cyan-800 dark:text-cyan-200",
  ARRIVED_AT_PORT: "border-teal-500/30 bg-teal-500/15 text-teal-800 dark:text-teal-200",
  CUSTOMS_CLEARANCE:
    "border-yellow-500/30 bg-yellow-500/15 text-yellow-900 dark:text-yellow-200",
  DELIVERED:
    "border-emerald-500/30 bg-emerald-500/15 text-emerald-900 dark:text-emerald-100",
  CANCELLED: "border-red-500/30 bg-red-500/15 text-red-800 dark:text-red-200",
};

const DEFAULT_STATUS_BADGE_CLASS =
  "border-[#546a7b]/65 bg-[#c6c5b9]/20 text-[#393d3f]";

export const getOrderStatusBadgeClass = (status: string): string =>
  ORDER_STATUS_BADGE_CLASSES[status] ?? DEFAULT_STATUS_BADGE_CLASS;

