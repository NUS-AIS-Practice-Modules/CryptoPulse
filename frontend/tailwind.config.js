/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "ui-sans-serif", "system-ui"],
        body: ["DM Sans", "ui-sans-serif", "system-ui"]
      },
      colors: {
        ink: "#0f172a",
        sand: "#f8f4ec",
        ember: "#c2410c",
        tide: "#0f766e",
        skyline: "#1d4ed8"
      },
      boxShadow: {
        panel: "0 20px 60px rgba(15, 23, 42, 0.12)"
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top right, rgba(29, 78, 216, 0.16), transparent 30%), radial-gradient(circle at bottom left, rgba(194, 65, 12, 0.12), transparent 28%)"
      }
    }
  },
  plugins: []
};
