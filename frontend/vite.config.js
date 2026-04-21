import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    outDir: path.resolve(__dirname, "../whatsapp_inbox/public/dist"),
    emptyOutDir: true,
    lib: {
      entry: path.resolve(__dirname, "src/main.js"),
      name: "WhatsAppInboxApp",
      fileName: "whatsapp_inbox",
      formats: ["iife"],
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {},
        assetFileNames: "whatsapp_inbox.[ext]",
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
});
