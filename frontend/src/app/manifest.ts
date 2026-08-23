import type { MetadataRoute } from "next";

// Web app manifest — auto-served at /manifest.webmanifest and auto-linked.
// This is what makes "Add to Home Screen" install Stocky as a standalone app
// (no browser chrome) with a dark splash instead of a white flash.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Stocky — Learn the market by using it",
    short_name: "Stocky",
    description:
      "A stock-market learning instrument. Scenario ranges, not predictions.",
    start_url: "/",
    display: "standalone",
    background_color: "#0A0B0D",
    theme_color: "#0A0B0D",
    icons: [
      // Static file in src/app/ — Next serves and auto-links it. (A dynamic
      // ImageResponse icon hits a Next-on-Windows dev bug: ERR_INVALID_URL
      // loading @vercel/og's bundled font — hence the committed PNG.)
      { src: "/apple-icon.png", sizes: "180x180", type: "image/png" },
    ],
  };
}
