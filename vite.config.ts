import { defineConfig } from "vite";

export default defineConfig({
  // GitHub Pages serves this project under /XAI-ElectricSheep/.
  // Local development and preview continue to use the site root.
  base: process.env.GITHUB_PAGES === "true" ? "/XAI-ElectricSheep/" : "/",
});
