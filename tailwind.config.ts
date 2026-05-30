import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Tokens DESIGN.md — palette Jarvis V2
      colors: {
        canvas: "#0B1020",
        "surface-soft": "#0F172A",
        "surface-card": "#111827",
        "surface-elevated": "#1A2235",
        "surface-input": "#1F2937",
        primary: "#4F46E5",
        "primary-active": "#4338CA",
        "primary-disabled": "#1E1B4B",
        "voice-active": "#00D4FF",
        "voice-glow": "#0EA5E9",
        "voice-muted": "#1E3A4A",
        ink: "#F9FAFB",
        body: "#D1D5DB",
        "body-strong": "#E5E7EB",
        muted: "#9CA3AF",
        "muted-soft": "#6B7280",
        hairline: "#1F2937",
        "hairline-soft": "#374151",
        "on-primary": "#FFFFFF",
        "on-voice": "#0B1020",
        "on-surface": "#F9FAFB",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        xs: "4px",
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        "2xl": "24px",
        pill: "999px",
      },
      animation: {
        breath: "breath 3s ease-in-out infinite",
        pulse: "pulse 1.5s ease-in-out infinite",
      },
      keyframes: {
        breath: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.8" },
          "50%": { transform: "scale(1.05)", opacity: "1" },
        },
      },
      maxWidth: {
        "2xl": "672px",
      },
    },
  },
  plugins: [],
};

export default config;
