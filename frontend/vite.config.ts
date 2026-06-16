import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts =
  process.env.VITE_ALLOW_NGROK_HOSTS === "1"
    ? true
    : ["localhost", "127.0.0.1", ".ngrok-free.app", ".ngrok-free.dev", ".ngrok.app", ".ngrok.pro"];

const backendProxyTarget = process.env.VITE_BACKEND_PROXY_TARGET || "http://127.0.0.1:18111";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts,
    proxy: {
      "/api": {
        target: backendProxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
