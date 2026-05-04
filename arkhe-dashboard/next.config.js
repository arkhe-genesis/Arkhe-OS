/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['@tensorflow/tfjs-node', 'sharp'],
  },
  serverExternalPackages: ['@tensorflow/tfjs-node', 'sharp'],
  transpilePackages: ['three'],
  env: {
    NEXT_PUBLIC_ARKHE_API_URL: process.env.NEXT_PUBLIC_ARKHE_API_URL || 'http://localhost:8000',
  },
  turbopack: {},
  webpack: (config, { isServer }) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
      crypto: require.resolve('crypto-browserify'),
      stream: require.resolve('stream-browserify'),
    };
    if (isServer) {
      config.externals.push('@tensorflow/tfjs-node');
    }
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
    };
    return config;
  },
};

module.exports = nextConfig;