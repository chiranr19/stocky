// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No ESLint config is shipped in this scaffold; don't block builds on it.
  eslint: { ignoreDuringBuilds: true },
  // Same-origin API proxy: the frontend calls /api/* and Next forwards to the
  // FastAPI backend on loopback. This is what lets a phone on the tailnet use
  // the app — "localhost:8010" would mean the phone itself. Desktop goes
  // through the same path, so behavior never diverges between devices.
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8010/:path*" }];
  },
};

export default nextConfig;
