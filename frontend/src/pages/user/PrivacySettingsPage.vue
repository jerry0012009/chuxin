<script setup lang="ts">
import {
  Book,
  Camera,
  ChevronLeft,
  ChevronRight,
  Eye,
  Fingerprint,
  Lock,
  MapPin,
  Shield,
} from 'lucide-vue-next'
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const statusMessage = ref('')
let statusTimer: number | null = null

const settings = reactive({
  twoFactor: false,
  profilePublic: true,
  dataSharing: false,
  cameraAccess: true,
  locationAccess: false,
  contactsAccess: false,
})

type SettingKey = keyof typeof settings

const toggleSetting = (key: SettingKey) => {
  settings[key] = !settings[key]
  if (statusTimer !== null) window.clearTimeout(statusTimer)
  statusMessage.value = '设置已更新'
  statusTimer = window.setTimeout(() => {
    statusMessage.value = ''
  }, 1800)
}

onBeforeUnmount(() => {
  if (statusTimer !== null) window.clearTimeout(statusTimer)
})

const permissionItems: Array<{
  key: SettingKey
  icon: typeof Camera
  label: string
  desc: string
  color: string
  bg: string
}> = [
  { key: 'cameraAccess', icon: Camera, label: '相机权限', desc: '用于拍照上传情绪记录', color: 'text-rose-500', bg: 'bg-rose-50 dark:bg-rose-950/30' },
  { key: 'locationAccess', icon: MapPin, label: '位置信息', desc: '记录情绪发生时的地理位置', color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-950/30' },
  { key: 'contactsAccess', icon: Book, label: '通讯录', desc: '发现使用初心的好友', color: 'text-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-950/30' },
]
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-10 dark:bg-slate-900">
    <div
      v-if="statusMessage"
      class="fixed left-1/2 top-[72px] z-[70] -translate-x-1/2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-xl shadow-slate-900/20"
      data-testid="privacy-toast"
    >
      {{ statusMessage }}
    </div>
    <div class="sticky top-0 z-10 flex items-center gap-4 bg-white px-4 py-4 shadow-sm dark:bg-slate-800">
      <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700" @click="router.back()">
        <ChevronLeft class="h-6 w-6" />
      </button>
      <h1 class="text-xl font-bold text-slate-900 dark:text-white">隐私与安全</h1>
    </div>

    <main class="mx-auto max-w-2xl space-y-4 p-4">
      <section class="space-y-2">
        <h2 class="px-1 text-sm font-semibold text-slate-500">账号安全</h2>
        <div class="overflow-hidden rounded-2xl bg-white shadow-sm dark:bg-slate-800">
          <button class="flex w-full items-center justify-between border-b border-slate-100 p-4 text-left dark:border-slate-700">
            <span class="flex items-center gap-3">
              <span class="rounded-lg bg-blue-50 p-2 text-blue-600 dark:bg-blue-950/30">
                <Lock class="h-5 w-5" />
              </span>
              <span>
                <span class="block font-medium text-slate-900 dark:text-white">修改登录密码</span>
                <span class="block text-xs text-slate-400">定期更换密码保障安全</span>
              </span>
            </span>
            <ChevronRight class="h-5 w-5 text-slate-300" />
          </button>
          <div class="flex items-center justify-between p-4">
            <div class="flex items-center gap-3">
              <span class="rounded-lg bg-purple-50 p-2 text-purple-600 dark:bg-purple-950/30">
                <Fingerprint class="h-5 w-5" />
              </span>
              <div>
                <div class="font-medium text-slate-900 dark:text-white">双重身份验证 (2FA)</div>
                <div class="text-xs text-slate-400">登录时需要额外的验证码</div>
              </div>
            </div>
            <button
              class="relative h-7 w-12 rounded-full transition"
              :class="settings.twoFactor ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'"
              data-testid="privacy-two-factor"
              role="switch"
              :aria-checked="settings.twoFactor"
              @click="toggleSetting('twoFactor')"
            >
              <span class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition" :class="settings.twoFactor ? 'left-6' : 'left-1'" />
            </button>
          </div>
        </div>
      </section>

      <section class="space-y-2">
        <h2 class="px-1 text-sm font-semibold text-slate-500">数据可见性</h2>
        <div class="overflow-hidden rounded-2xl bg-white shadow-sm dark:bg-slate-800">
          <div class="flex items-center justify-between border-b border-slate-100 p-4 dark:border-slate-700">
            <div class="flex items-center gap-3">
              <span class="rounded-lg bg-emerald-50 p-2 text-emerald-600 dark:bg-emerald-950/30">
                <Eye class="h-5 w-5" />
              </span>
              <div>
                <div class="font-medium text-slate-900 dark:text-white">公开个人资料</div>
                <div class="text-xs text-slate-400">允许其他用户查看您的基本信息</div>
              </div>
            </div>
            <button
              class="relative h-7 w-12 rounded-full transition"
              :class="settings.profilePublic ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'"
              data-testid="privacy-profile-public"
              role="switch"
              :aria-checked="settings.profilePublic"
              @click="toggleSetting('profilePublic')"
            >
              <span class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition" :class="settings.profilePublic ? 'left-6' : 'left-1'" />
            </button>
          </div>
          <div class="flex items-center justify-between p-4">
            <div class="flex items-center gap-3">
              <span class="rounded-lg bg-amber-50 p-2 text-amber-600 dark:bg-amber-950/30">
                <Shield class="h-5 w-5" />
              </span>
              <div>
                <div class="font-medium text-slate-900 dark:text-white">匿名化健康数据共享</div>
                <div class="text-xs text-slate-400">用于医学研究，不包含身份信息</div>
              </div>
            </div>
            <button
              class="relative h-7 w-12 rounded-full transition"
              :class="settings.dataSharing ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'"
              data-testid="privacy-data-sharing"
              role="switch"
              :aria-checked="settings.dataSharing"
              @click="toggleSetting('dataSharing')"
            >
              <span class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition" :class="settings.dataSharing ? 'left-6' : 'left-1'" />
            </button>
          </div>
        </div>
      </section>

      <section class="space-y-2">
        <h2 class="px-1 text-sm font-semibold text-slate-500">应用权限管理</h2>
        <div class="overflow-hidden rounded-2xl bg-white shadow-sm dark:bg-slate-800">
          <div
            v-for="(item, index) in permissionItems"
            :key="item.key"
            class="flex items-center justify-between p-4"
            :class="index !== permissionItems.length - 1 ? 'border-b border-slate-100 dark:border-slate-700' : ''"
          >
            <div class="flex items-center gap-3">
              <span class="rounded-lg p-2" :class="[item.bg, item.color]">
                <component :is="item.icon" class="h-5 w-5" />
              </span>
              <div>
                <div class="font-medium text-slate-900 dark:text-white">{{ item.label }}</div>
                <div class="text-xs text-slate-400">{{ item.desc }}</div>
              </div>
            </div>
            <button
              class="relative h-7 w-12 rounded-full transition"
              :class="settings[item.key] ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'"
              :data-testid="`privacy-${item.key}`"
              role="switch"
              :aria-checked="settings[item.key]"
              @click="toggleSetting(item.key)"
            >
              <span class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition" :class="settings[item.key] ? 'left-6' : 'left-1'" />
            </button>
          </div>
        </div>
      </section>

      <div class="px-1 pt-6">
        <button class="h-auto p-0 text-sm font-medium text-blue-600">
          查看详细《隐私政策与服务协议》
        </button>
        <p class="mt-2 text-[10px] leading-relaxed text-slate-400">
          初心严格遵守 GDPR、CCPA 等全球隐私法规，您的数据始终在您的控制之下。我们使用 AES-256 加密技术保障您的个人隐私安全。
        </p>
      </div>
    </main>
  </div>
</template>
