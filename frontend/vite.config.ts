import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Phase 1 skeleton config. PWA plugin (manifest, service worker, offline
// caching) will be added when the design system / real screens land.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    target: "es2020",
    // No sourcemaps in the shipped production bundle: they make debugging
    // easier but also hand an attacker a readable copy of the source.
    sourcemap: false,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // Split the React runtime into its own long-lived cache chunk so a
        // normal app-code deploy doesn't force everyone to re-download React.
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
});
