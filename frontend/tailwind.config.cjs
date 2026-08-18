/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        ink: "#0B1226",
        paper: "#F6F8FC",
        violet: { 500: "#3B82F6", 600: "#2563EB" },
        flame: { 500: "#06B6D4", 600: "#0891B2" },
      },
      boxShadow: {
        soft: "0 8px 24px -8px rgba(37, 99, 235, 0.20), 0 2px 6px -2px rgba(37, 99, 235, 0.08)",
        glow: "0 16px 48px -12px rgba(37, 99, 235, 0.40), 0 8px 24px -8px rgba(6, 182, 212, 0.22)",
        ring: "0 0 0 1px rgba(37, 99, 235, 0.10)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "50%": { transform: "translateY(-12px) rotate(2deg)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        drift: {
          "0%, 100%": { transform: "translate3d(0,0,0) scale(1)" },
          "33%": { transform: "translate3d(40px,-30px,0) scale(1.06)" },
          "66%": { transform: "translate3d(-30px,20px,0) scale(0.94)" },
        },
        spinSlow: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        shimmer: "shimmer 2.4s linear infinite",
        float: "float 6s ease-in-out infinite",
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
        drift: "drift 22s ease-in-out infinite",
        spinSlow: "spinSlow 60s linear infinite",
      },
    },
  },
  plugins: [],
};
