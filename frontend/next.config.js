/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    NEXT_PUBLIC_APP_NAME: 'NEXORA AI',
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
  webpack: (config, { isServer }) => {
    // Disable symlink resolution on FAT32 filesystems where readlink throws EISDIR
    config.resolve.symlinks = false;
    return config;
  }
};

module.exports = nextConfig;
