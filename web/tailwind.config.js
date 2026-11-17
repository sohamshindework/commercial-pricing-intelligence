/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F7F4F0",
        surface: "#FFFFFF",
        "surface-alt": "#F0EBF3",
        ink: "#2F2941",
        body: "#51495F",
        muted: "#777184",
        border: "#E8E1E8",
        iris: { DEFAULT: "#6653A3", hover: "#514187" },
        lilac: "#C5B6E1",
        coral: "#DC8B73",
        sage: "#91ADAA",
        positive: "#437F72",
        negative: "#B75B68",
        warning: "#B17A43",
      },
      fontFamily: {
        heading: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        body: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        kpi: ["30px", { lineHeight: "1.1", fontWeight: "600" }],
      },
      borderRadius: { card: "12px" },
      boxShadow: { card: "0 1px 2px rgba(49, 45, 67, 0.05)" },
    },
  },
  plugins: [],
};
