import sriResources from "@/sri-resources.json";

type MatchType = "exact" | "startsWith";

type SriResource = {
  name: string;
  url: string;
  integrity: string;
  crossorigin?: string;
  match?: MatchType;
};

type SriAttributes = {
  integrity?: string;
  crossOrigin?: string;
};

const resources = (sriResources.resources as SriResource[]).map((resource) => ({
  ...resource,
  match: resource.match ?? "exact",
}));

export function getSriAttributes(url: string): SriAttributes {
  const resource = resources.find((entry) => {
    if (entry.match === "startsWith") {
      return url.startsWith(entry.url);
    }
    return url === entry.url;
  });

  if (
    !resource ||
    !resource.integrity ||
    resource.integrity.includes("REPLACE_WITH_HASH")
  ) {
    return {};
  }

  return {
    integrity: resource.integrity,
    crossOrigin: resource.crossorigin ?? "anonymous",
  };
}

export function listSriResources(): SriResource[] {
  return resources;
}
