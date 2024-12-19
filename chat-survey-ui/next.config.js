/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@epistemicme/sdk"],
  webpack: (config) => {
    config.resolve.extensionAlias = {
      '.js': ['.js', '.ts']
    }
    return config
  }
}

module.exports = nextConfig 