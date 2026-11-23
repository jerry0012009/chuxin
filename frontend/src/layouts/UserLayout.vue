<script setup lang="ts">
import { Activity, Brain, BrainCircuit, ClipboardList, Heart, Home, ListChecks, User } from 'lucide-vue-next'
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useMedia } from '@/composables/useMedia'
import { useAppState } from '@/composables/useAppState'
import { useAuthSession } from '@/composables/useAuthSession'
import { resolveAvatarSource } from '@/lib/avatar-presets'
import ServiceMasthead from '@/components/ui/ServiceMasthead.vue'

const logoSrc = `${import.meta.env.BASE_URL}logo.jpg`

const route = useRoute()
const router = useRouter()
const { isMobile } = useMedia()
const { refreshCurrentAccountProfile } = useAppState()
const { state: authState } = useAuthSession()

const navItems = [
  { path: '/', label: '首页', icon: Home },
  { path: '/assessment-tasks', label: '任务中心', icon: ListChecks },
  { path: '/scale-assessment', label: '量表测评', icon: ClipboardList },
  { path: '/assessment', label: '多模态评估', icon: Activity },
  { path: '/neuropsych-assessment', label: '神经心理', icon: Brain },
  { path: '/brain-intervention', label: '脑机调控', icon: BrainCircuit },
  { path: '/healing', label: '疗愈', icon: Heart },
  { path: '/profile', label: '我的', icon: User },
]

const currentPath = computed(() => route.path)
const servicePage = computed(() => currentPath.value === '/' || isActiveNav('/assessment-tasks'))
const serviceItems = [
  { path: '/', label: '我的工作台', icon: Home },
  { path: '/assessment-tasks', label: '测评任务', icon: ListChecks },
  { path: '/profile/healing-plan', label: '疗愈计划', icon: Heart },
  { path: '/profile', label: '个人中心', icon: User },
]
const isActiveNav = (path: string) => {
  if (path === '/') return currentPath.value === '/'
  return currentPath.value === path || currentPath.value.startsWith(`${path}/`)
}
const avatarSource = computed(() => resolveAvatarSource(authState.profile?.avatar_url))
const displayName = computed(() => authState.profile?.full_name || authState.profile?.username || '用户登录')

onMounted(() => {
  void refreshCurrentAccountProfile().catch(() => {
    // Background refresh can be cancelled by route changes; user-facing actions report their own failures.
  })
})

const handleLogoClick = () => {
  window.location.href = window.location.pathname || '/'
}
</script>

<template>
  <div v-if="servicePage" class="service-page">
    <ServiceMasthead />
    <nav class="service-nav" aria-label="用户服务">
      <div class="service-width service-nav-inner">
        <RouterLink v-for="item in serviceItems" :key="item.path" :to="item.path" :aria-current="isActiveNav(item.path) ? 'page' : undefined">
          <component :is="item.icon" class="hidden h-4 w-4 sm:block" aria-hidden="true" />{{ item.label }}
        </RouterLink>
      </div>
    </nav>
    <main><RouterView /></main>
  </div>
  <div v-else class="min-h-screen bg-background">
    <aside
      v-if="!isMobile"
      class="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-white/70 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80"
    >
      <button class="group w-full border-b border-white/70 p-6 text-left transition hover:scale-[1.01] dark:border-slate-800" type="button" @click="handleLogoClick">
        <div class="flex items-center gap-2">
          <div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl">
            <img alt="初心" class="h-full w-full object-contain" :src="logoSrc" />
          </div>
          <div>
            <p class="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 bg-clip-text text-xl font-bold text-transparent">初心</p>
            <p class="text-xs text-slate-500">智能心理健康助手</p>
          </div>
        </div>
      </button>

      <nav class="flex-1 space-y-2 p-4">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition"
          :class="
            isActiveNav(item.path)
              ? 'bg-gradient-to-r from-blue-500 to-cyan-400 text-white shadow-lg shadow-blue-500/25'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
          "
        >
          <component :is="item.icon" class="h-5 w-5" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="mt-auto">
        <div class="border-t border-white/70 p-4 dark:border-slate-800">
          <button
            class="flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-medium text-slate-900 transition hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
            type="button"
            @click="router.push('/login')"
          >
            <img v-if="avatarSource.imageUrl" :src="avatarSource.imageUrl" alt="头像" class="h-8 w-8 rounded-full border-2 border-slate-200 object-cover dark:border-slate-700" />
            <span v-else :class="['flex h-8 w-8 items-center justify-center rounded-full border-2 border-slate-200 text-xs dark:border-slate-700', avatarSource.preset?.bg || 'bg-primary/10 text-primary']">
              {{ avatarSource.preset?.emoji || authState.profile?.full_name?.charAt(0) || authState.profile?.username?.charAt(0) || 'U' }}
            </span>
            <span class="truncate">{{ displayName }}</span>
          </button>
        </div>
        <div class="border-t border-white/70 p-4 dark:border-slate-800">
          <div class="rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 px-4 py-3 text-center text-xs text-slate-500 dark:from-purple-950/20 dark:to-pink-950/20 dark:text-slate-400">
          © 2026 初心
          </div>
        </div>
      </div>
    </aside>

    <main :class="isMobile ? 'pb-20' : 'ml-64 min-h-screen'">
      <RouterView />
    </main>

    <nav
      v-if="isMobile"
      class="mobile-safe fixed inset-x-0 bottom-0 z-50 border-t border-white/70 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95"
    >
      <div class="mx-auto flex h-16 max-w-screen-xl items-center overflow-x-auto px-1 scrollbar-hide">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex h-full min-w-[58px] flex-1 flex-col items-center justify-center gap-1 text-[10px]"
          :class="isActiveNav(item.path) ? 'text-primary' : 'text-slate-400 dark:text-slate-500'"
        >
          <component :is="item.icon" class="h-5 w-5" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
