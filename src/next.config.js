/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable ESLint during production builds to prevent build failures on
  // missing or misconfigured rules. This setting tells Next.js to skip
  // running ESLint when `next build` is executed on Vercel or in CI.
  // See https://nextjs.org/docs/app/building-your-application/configuring#eslint
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Vercel free tier: serverless functions have 10s max duration
  // We handle this with timeouts in our API routes
  experimental: {
    serverComponentsExternalPackages: ['cheerio'],
  },
}

module.exports = nextConfig
