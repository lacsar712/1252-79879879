import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')
    const port = parseInt(env.FRONTEND_PORT || '3000', 10)
    const host = env.FRONTEND_HOST || '0.0.0.0'
    const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

    return {
        plugins: [vue()],
        resolve: {
            alias: {
                '@': resolve(__dirname, 'src')
            }
        },
        server: {
            host,
            port,
            proxy: {
                '/api': {
                    target: apiProxyTarget,
                    changeOrigin: true,
                    rewrite: (path) => path
                },
                '/docs': {
                    target: apiProxyTarget,
                    changeOrigin: true
                },
                '/redoc': {
                    target: apiProxyTarget,
                    changeOrigin: true
                },
                '/openapi.json': {
                    target: apiProxyTarget,
                    changeOrigin: true
                }
            }
        }
    }
})
