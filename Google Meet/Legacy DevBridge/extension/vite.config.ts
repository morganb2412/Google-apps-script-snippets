import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    rollupOptions: { input: { sidepanel: "index.html", background: "src/background/index.ts" } },
  },
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"] },
});
