import path from 'path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['@epistemicme/sdk'],
  experimental: {
    externalDir: true
  },
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...config.resolve.alias,
      '@epistemicme/sdk': path.resolve(__dirname, '../../Typescript-SDK/src')
    };
    return config;
  }
};

export default nextConfig;