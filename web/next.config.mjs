/** @type {import('next').NextConfig} */
const API = process.env.API_URL || "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    // Proxy backend calls to FastAPI. (/api/* is reserved for Next's own routes, e.g. auth.)
    return [{ source: "/backend/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
