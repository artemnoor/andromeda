import { defineConfig } from "vite";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/programs": apiProxyTarget,
      "/compare": apiProxyTarget,
      "/proftest": apiProxyTarget,
      "/recommendations": apiProxyTarget,
      "/events": apiProxyTarget,
      "/personal-route": apiProxyTarget,
      "/ops": apiProxyTarget,
      "/auth": apiProxyTarget,
      "/openapi.json": apiProxyTarget,
      "/docs": apiProxyTarget,
    }
  }
});
