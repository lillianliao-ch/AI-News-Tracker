const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [
      require('remark-gfm'),
    ],
    rehypePlugins: [
      require('rehype-slug'),
      require('rehype-highlight'),
    ],
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 配置MDX文件扩展
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],
  
  // 实验性功能
  experimental: {
    mdxRs: false,
  },

  // 图片配置
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // 重定向配置
  async redirects() {
    return [
      {
        source: '/blog',
        destination: '/blog/page/1',
        permanent: false,
      },
    ];
  },
};

module.exports = withMDX(nextConfig);