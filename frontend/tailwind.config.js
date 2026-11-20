/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          DEFAULT: "#060913",
          card: "#0c1222",
          surface: "#131b31",
          border: "#1e293b",
        },
        cyber: {
          DEFAULT: "#a3e635", // Cyber Lime
          hover: "#84cc16",
          glow: "rgba(163, 230, 53, 0.15)",
        },
        violet: {
          tech: "#8b5cf6", // Tech Violet
          hover: "#7c3aed",
          glow: "rgba(139, 92, 246, 0.15)",
        },
        text: {
          primary: "#f8fafc",
          secondary: "#94a3b8",
          muted: "#64748b",
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      boxShadow: {
        "cyber-glow": "0 0 20px -5px rgba(163, 230, 53, 0.3)",
        "tech-glow": "0 0 20px -5px rgba(139, 92, 246, 0.3)",
      }
    },
  },
  plugins: [],
};
