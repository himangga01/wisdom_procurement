import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts =
  process.env.VITE_ALLOW_NGROK_HOSTS === "1" ? true : ["localhost", "127.0.0.1", ".ngrok-free.app"];

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts,
  },
});
