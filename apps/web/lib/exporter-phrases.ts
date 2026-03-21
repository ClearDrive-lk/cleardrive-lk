export const EXPORTER_TERMS = {
  opsBadge: "ClearDrive Export Ops",
  actionRequired: "Action Required",
  bookingRef: "Booking Reference",
  billOfLading: "Bill of Lading (B/L)",
  containerNo: "Container No.",
  sealNo: "Seal No.",
  portOfLoading: "Port of Loading",
  portOfDischarge: "Port of Discharge",
  etd: "ETD (Departure)",
  eta: "ETA (Arrival)",
  transitMilestone: "Transit Milestone",
  customsReady: "Customs Clearance Ready",
} as const;

export type ExporterOrderFilter =
  | "all"
  | "action_required"
  | "in_transit"
  | "delivered";
