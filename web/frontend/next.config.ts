import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 압축 활성화
  compress: true,

  // 개발 인디케이터 숨김
  devIndicators: {
    buildActivity: false,
  },

  // 이미지 최적화
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // 프로덕션 최적화
  productionBrowserSourceMaps: false,
  poweredByHeader: false,

  // Turbopack 설정 (Next.js 16+)
  turbopack: {},

  // 실험적 기능
  experimental: {
    optimizePackageImports: ['recharts', 'lucide-react'],
  },

  // 프로덕션 빌드용 webpack 설정 (Turbopack 사용 안 함)
  ...(process.env.NODE_ENV === 'production' && {
    webpack: (config, { dev, isServer }) => {
      if (!dev && !isServer) {
        config.optimization = {
          ...config.optimization,
          moduleIds: 'deterministic',
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              default: false,
              vendors: false,
              commons: {
                name: 'commons',
                chunks: 'all',
                minChunks: 2,
                priority: 10,
              },
              recharts: {
                test: /[\\/]node_modules[\\/](recharts)[\\/]/,
                name: 'recharts',
                priority: 20,
              },
              ui: {
                test: /[\\/]node_modules[\\/](@radix-ui)[\\/]/,
                name: 'ui',
                priority: 15,
              },
            },
          },
        };
      }
      return config;
    },
  }),
};

export default nextConfig;
