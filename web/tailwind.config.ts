import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#151915",
        paper: "#FAFBF8",
        mist: "#EEF2EF",
        line: "#D8DED8",
        pine: "#2F6B57",
        leaf: "#7FA36A",
        berry: "#A33D55",
        citron: "#D5E271",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "Helvetica", "sans-serif"],
        serif: ["Georgia", "Times New Roman", "serif"],
      },
      boxShadow: {
        soft: "0 18px 60px rgba(21, 25, 21, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
