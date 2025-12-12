// next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  images: {
    domains: [],
  },
  async redirects() {
    return [];
  },
};

module.exports = nextConfig;