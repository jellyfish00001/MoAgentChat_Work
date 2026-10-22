/** @type {import('next').NextConfig} */
const nextConfig = {
  // [ai_prepare 修改] standalone：build 出只含執行必要檔案的 server.js，image 小很多
  output: "standalone",
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
