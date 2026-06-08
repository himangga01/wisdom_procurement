import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: process.env.VITE_ALLOW_NGROK_HOSTS === "1" ? true : undefined,
  },
});
