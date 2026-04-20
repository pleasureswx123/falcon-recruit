/** @type {import('next').NextConfig} */
const nextConfig = {
  // 容器化构建使用 standalone 输出，显著缩小镜像体积
  output: "standalone",
};

export default nextConfig;
