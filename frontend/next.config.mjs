/** @type {import('next').NextConfig} */
const nextConfig = {
  // 容器化构建使用 standalone 输出，显著缩小镜像体积
  output: "standalone",
  
  // 开发环境 API 代理（解决跨域问题）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
