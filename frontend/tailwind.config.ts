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
        faint: "#5A616B",
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
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
