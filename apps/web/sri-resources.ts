export const sriResources = {
  resources: [
    {
      name: "Google Identity Services",
      url: "https://accounts.google.com/gsi/client",
      integrity:
        "sha384-C2U10A7D9SJwz7wVqySblUJgA6VKd9Ff2poBlQ1shkWrAnrJNMctvgwkJEL04fF9", // pragma: allowlist secret
      crossorigin: "anonymous",
      match: "exact",
    },
    {
      name: "Google Analytics gtag",
      url: "https://www.googletagmanager.com/gtag/js",
      integrity:
        "sha384-0cC1Z+/Bu60uM6AJnefz3sAPWA7V+jL7i5spNij5Fyynf2K1KwQ4BdD68xv1nFxm", // pragma: allowlist secret
      crossorigin: "anonymous",
      match: "startsWith",
    },
  ],
} as const;
