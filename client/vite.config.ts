import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

import path from "path";
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/vitest.setup.mjs",
    globals: true,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@context": path.resolve(__dirname, "./src/context"),
      "@components": path.resolve(__dirname, "./src/components"),
      "@pages": path.resolve(__dirname, "./src/pages"),
      "@layout": path.resolve(__dirname, "./src/layout"),
      "@tests": path.resolve(__dirname, "./__tests__"),
    },
  },
});
