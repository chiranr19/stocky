// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
import type { Config } from "tailwindcss";

// Dark fintech palette — Linear/Raycast energy. Semantic names so components
// read cleanly (bg-panel, text-up, border-hair, …).
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0B0D",
        panel: "#0F1114",
        elevated: "#15181D",
        hair: "rgba(255,255,255,0.07)",
        ink: "#E7E9EC",
        muted: "#8B929C",
        // Quietest text that still passes AA at small sizes on the panels
        // (#5A616B measured ~3.0:1 — illegible at 10px on a phone; this is
        // ~4.9:1 while staying a clear step below `muted`).
        faint: "#7A8290",
        up: "#22C989",
        down: "#F6465D",
        accent: "#7C6BFF",
        "accent-dim": "#4A3FA8",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
        glow: "0 0 0 1px rgba(124,107,255,0.35), 0 8px 40px -8px rgba(124,107,255,0.35)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "grow-bar": {
          from: { transform: "scaleX(0)" },
          to: { transform: "scaleX(1)" },
        },
        "pop-in": {
          from: { opacity: "0", transform: "scale(0.6)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
        "grow-bar": "grow-bar 0.5s ease-out both",
        "pop-in": "pop-in 0.25s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
