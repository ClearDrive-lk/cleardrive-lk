import { dirname } from "path";
import { fileURLToPath } from "url";
import type { Configuration } from "webpack";
import { SubresourceIntegrityPlugin } from "webpack-subresource-integrity";

const appDir = dirname(fileURLToPath(import.meta.url));

const nextConfig = {
  turbopack: {
    root: appDir,
  },
  images: {
    dangerouslyAllowLocalIP: true,
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "localhost" },
      { protocol: "http", hostname: "localhost" },
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "www.ramadbk.com" },
      { protocol: "https", hostname: "**.supabase.co" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/v1/:path*", // Proxy to Backend
      },
    ];
  },

  webpack: (
    config: Configuration,
    { dev, isServer }: { dev: boolean; isServer: boolean },
  ) => {
    if (!dev && !isServer) {
      config.output = {
        ...(config.output ?? {}),
        crossOriginLoading: "anonymous",
      };
      config.plugins = config.plugins ?? [];
      config.plugins.push(
        new SubresourceIntegrityPlugin({
          hashFuncNames: ["sha384"],
          enabled: true,
        }),
      );
    }
    return config;
  },

  // ⭐ REQUIRED FOR FEDCM
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Permissions-Policy",
            value: "identity-credentials-get=(self)",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
