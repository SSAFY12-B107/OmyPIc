import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico'],
      manifest: {
        name: 'OmyPIc',
        short_name: 'OmyPIc',
        description: '단기 고득점 오픽 취득',
        theme_color: '#9466E9',
        icons: [
          {
            src: 'web-app-manifest-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'web-app-manifest-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'web-app-manifest-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      // API 요청 처리를 위한 Workbox 설정 추가
      workbox: {
        // API와 docs 경로를 서비스 워커의 기본 처리에서 제외
        navigateFallbackDenylist: [/^\/api\//, /^\/docs\//],
        
        // 런타임 캐싱 전략 설정
        runtimeCaching: [
          {
            // 개발 환경과 프로덕션 환경의 API URL 모두 처리
            urlPattern: ({ url }) => {
              return url.pathname.startsWith('/api') || 
                     url.origin === 'https://omypic.store' && url.pathname.startsWith('/api') ||
                     url.origin === 'http://localhost:8000' && url.pathname.startsWith('/api');
            },
            handler: 'NetworkOnly', // API 요청은 항상 네트워크로 직접 전송
            options: {
              backgroundSync: {
                name: 'api-queue',
                options: {
                  maxRetentionTime: 24 * 60 // 최대 보관 시간(분)
                }
              }
            }
          },
          {
            // 정적 자산(이미지, CSS, JS 등)에 대한 캐싱 전략
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|js|css|woff2)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'assets-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30일
              }
            }
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // '@'를 src 경로로 설정
    },
  },
})