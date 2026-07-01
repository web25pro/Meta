/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Transpile the workspace design system + shared types (Meta-Jungle monorepo).
  transpilePackages: ['@meta-jungle/ui', '@meta-jungle/types'],
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://meta-4bck.onrender.com/api/v1',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://meta-4bck.onrender.com/api/v1'}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
