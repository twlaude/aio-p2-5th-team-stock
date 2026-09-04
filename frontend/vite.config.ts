import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendUrl = env.VITE_BACKEND_URL || "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: 8501,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: 8501,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    test: {
      globals: false,
      include: ["tests/**/*.test.ts"],
    },
  };
});
