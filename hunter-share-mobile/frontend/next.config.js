/** @type {import('next').NextConfig} */
const nextConfig = {
  // 禁用严格模式以避免开发环境的重复渲染
  reactStrictMode: false,
  
  // API代理配置
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;

