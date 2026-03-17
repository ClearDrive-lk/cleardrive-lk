export const normalizeRole = (role?: string | null) => {
  if (!role) return "CUSTOMER";
  const normalized = role.trim().toUpperCase();
  if (normalized === "USER") return "CUSTOMER";
  return normalized;
};

export const roleHomePath = (role?: string | null) => {
  const normalized = normalizeRole(role);
  if (normalized === "ADMIN") return "/admin/dashboard";
  if (normalized === "EXPORTER") return "/exporter";
  return "/dashboard";
};

export const isRole = (role: string | null | undefined, match: string) =>
  normalizeRole(role) === match;
