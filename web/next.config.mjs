/** @type {import('next').NextConfig} */
const API = process.env.API_URL || "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    // Proxy API calls to the FastAPI backend (same-origin in the browser).
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
