import { fileURLToPath, URL } from 'node:url'
import { existsSync, readFileSync } from 'node:fs'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const productionEnv = readEnvFile('.env.production')
const appBase = process.env.VITE_APP_BASE || productionEnv.VITE_APP_BASE || '/'

// https://vite.dev/config/
export default defineConfig({
  base: appBase,
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})

function readEnvFile(path: string) {
  if (!existsSync(path)) return {} as Record<string, string>
  return Object.fromEntries(
    readFileSync(path, 'utf8')
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith('#') && line.includes('='))
      .map((line) => {
        const index = line.indexOf('=')
        return [line.slice(0, index), line.slice(index + 1)]
      }),
  )
}
