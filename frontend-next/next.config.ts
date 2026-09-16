import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: false,
  allowedDevOrigins: ["localhost", "127.0.0.1"],
};

if (process.env.NODE_ENV === "development") {
  console.info("[FIX:frontend-origin] Next dev origins enabled for localhost and 127.0.0.1");
}

export default nextConfig;
