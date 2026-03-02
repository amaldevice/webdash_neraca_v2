/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./templates/partials/**/*.html",
    "./app.py",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        bps: {
          "primary": "#0B5ED7",
          "primary-content": "#ffffff",
          "accent": "#F97316",
          "accent-content": "#111827",
          "neutral": "#E2E8F0",
          "neutral-content": "#0F172A",
          "base-100": "#F8FAFC",
          "base-200": "#E2E8F0",
          "base-300": "#CBD5E1",
          "base-content": "#0F172A",
          "info": "#38BDF8",
          "success": "#22C55E",
          "warning": "#F59E0B",
          "error": "#EF4444"
        }
      },
      {
        "bps-dark": {
          "primary": "#0B5ED7",
          "primary-content": "#ffffff",
          "accent": "#F97316",
          "accent-content": "#0B1220",
          "neutral": "#1F2937",
          "neutral-content": "#E5E7EB",
          "base-100": "#0B1220",
          "base-200": "#111827",
          "base-300": "#1F2937",
          "base-content": "#E5E7EB",
          "info": "#38BDF8",
          "success": "#22C55E",
          "warning": "#F59E0B",
          "error": "#EF4444"
        }
      }
    ],
    darkTheme: "bps-dark"
  }
};
