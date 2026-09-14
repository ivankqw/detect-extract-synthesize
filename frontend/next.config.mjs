/** @type {import('next').NextConfig} */

const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: '/backend/:path*',
        // destination: 'http://localhost:8000/backend/:path*', //proxy to fastapi
        destination: 'https://fyp-backend-ynjpgkkhnq-uc.a.run.app/backend/:path*',
      },
    ];
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'canvas': false,
    };

    return config;
  },
  serverExternalPackages: ['@react-pdf/renderer'],
  redirects: async () => {
    return [
      {
        source: '/docs-search',
        destination: '/docs',
        permanent: true,
      },
    ]
  }
};

export default nextConfig;
