import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/programs": "http://127.0.0.1:8000",
      "/compare": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000"
    }
  }
});
