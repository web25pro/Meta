/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Transpile the workspace design system + shared types (Meta-Jungle monorepo).
  transpilePackages: ['@meta-jungle/ui', '@meta-jungle/types'],
  // Backend URL is NOT exposed to the browser — it lives in BACKEND_URL
  // (server-side only) and is used by the API proxy at /api/[...path]/route.ts.
};

module.exports = nextConfig;
