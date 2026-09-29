import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const sourceDir = import.meta.dirname ?? ".";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": `${sourceDir}/src`,
      cn: `${sourceDir}/src/lib/utils`,
    },
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          const vendor = id.includes("node_modules");
          if (vendor && (id.includes("recharts") || id.includes("d3-") || id.includes("victory-vendor"))) {
            return "recharts";
          }
          return undefined;
        },
      },
    },
  },
});
