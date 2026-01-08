import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import fs from "fs";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 1. Read Backend Port dynamically
  let backendPort = 8000; // Default
  try {
    const envPath = path.resolve(__dirname, "../backend/.env");
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, "utf-8");
      const match = envContent.match(/^PORT=(\d+)/m);
      if (match) {
        backendPort = parseInt(match[1], 10);
      }
    }
  } catch (e) {
    // Ignore error, use default
  }

  const backendUrl = `http://localhost:${backendPort}`;

  return {
    server: {
      host: "::",
      port: 5173,
    },
    // 2. Inject the dynamic URL
    define: {
      'import.meta.env.VITE_BACKEND_URL': JSON.stringify(backendUrl),
    },
    plugins: [react()].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
