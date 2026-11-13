/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // 真机联调（手机通过局域网 IP 访问 dev 站）：Next 16 的 cross-site 防护会把
  // 来自未登记来源的 HMR WebSocket 挡掉，表现是页面停在骨架屏、一个 API 都不发
  // ——不是白屏报错。默认放行 192.168.x.x，其他网段用 DEV_ALLOWED_ORIGINS
  // （逗号分隔，支持 `*` 通配段）覆盖。
  allowedDevOrigins: (process.env.DEV_ALLOWED_ORIGINS || "192.168.*.*").split(","),
  // dev 指示器：**整个关掉**，不是挪到右下角。
  // 默认 `bottom-left` 的 36×36 指示器正好压在观看页底栏「上一句」的中心点上（实测
  // `elementFromPoint(52, 868)` = `NEXTJS-PORTAL`），真机联调与本地自动化都会被它吞掉点击。
  // 挪 `bottom-right` 只是把同一个问题搬给「跟读」那一格 —— 实测 414 档底栏四等分后右下角
  // 正是 `watch-shadowing` 的中心，命中测试照样红。底栏是铺满整宽的四个键，四角没有一个
  // 位置不压按钮，所以唯一能同时保住真机可点性与自动化判据的取值是 `false`。
  // 编译/运行时错误浮层不受影响（Next 仍会显示）。
  devIndicators: false,
  experimental: {
    // Rewrite barrel-file imports (recharts, lucide-react) into direct,
    // tree-shakeable imports to keep unused chart/icon code out of bundles.
    optimizePackageImports: ["recharts", "lucide-react"],
  },
  // In development, proxy /api/ and /media/ to the backend so the frontend
  // can use relative paths without nginx. Production standalone output ignores
  // rewrites — nginx handles the proxying there.
  async rewrites() {
    if (process.env.NODE_ENV === "development") {
      // 显式 127.0.0.1 而不是 localhost：本机文档里的 uvicorn 一律绑 IPv4
      // （0.0.0.0 / 127.0.0.1），而 Node 的 `localhost` 会先尝试 ::1。写出实际
      // 端点，代理行为就不再依赖平台的解析顺序。
      //
      // BACKEND_PROXY_ORIGIN 覆盖它：docker-compose.yml 的 dev 全栈把 frontend
      // 也跑在容器里，此时容器内的 127.0.0.1 是 frontend 自己，必须指向 compose
      // 服务名。默认值保持 127.0.0.1，本机原生开发行为不变。
      const backend = process.env.BACKEND_PROXY_ORIGIN || "http://127.0.0.1:8000";
      return [
        { source: "/api/:path*", destination: `${backend}/api/:path*` },
        { source: "/media/:path*", destination: `${backend}/media/:path*` },
        { source: "/health", destination: `${backend}/health` },
      ];
    }
    return [];
  },
  images: {
    // 完全绕过 Next 优化器：生产 standalone server 上没有 /media 路由，优化器
    // 的服务端抓取会失败（拿到 Next 自己的 404 页）；缩略图已由后端管线生成尺寸，
    // 跳过优化没有成本。`unoptimized` 让 next/image 直接输出原始 src —— 之前用
    // 自定义 loader 达到同样效果，但 loader 不实现 width 会在 dev 触发
    // next-image-missing-loader-width 警告（每个 <Image> 一条）。
    unoptimized: true,
    localPatterns: [
      // /media/ paths proxied to backend (thumbnails, avatars, etc.)
      // Next 16+ requires localPatterns for local images with query strings.
      // Omitting `search` skips query-string validation (allows any ?...).
      { pathname: "/media/**" },
    ],
    remotePatterns: [
      // Direct CDN hosts — fallback for URLs not routed through mediaUrl's proxy.
      { protocol: "https", hostname: "**.aliyuncs.com" },
      { protocol: "https", hostname: "**.ytimg.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
      { protocol: "https", hostname: "**.hdslb.com" },
      { protocol: "https", hostname: "**.biliimg.com" },
      { protocol: "https", hostname: "**.douyinpic.com" },
      { protocol: "https", hostname: "**.douyincdn.com" },
      { protocol: "https", hostname: "**.douyinstatic.com" },
    ],
  },
};

module.exports = nextConfig;
