/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    resolveAlias: {
      "@/*": "./*",
    },
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "localhost" },
<<<<<<< HEAD
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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
