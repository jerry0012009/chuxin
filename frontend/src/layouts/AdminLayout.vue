<script setup lang="ts">
import {
  AlertTriangle,
  BookOpen,
  Brain,
  Building2,
  ClipboardList,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Send,
  Users,
} from 'lucide-vue-next'
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthSession } from '@/composables/useAuthSession'
import type { Component } from 'vue'
import type { UserRole } from '@/types'

type AdminNavItem = {
  path: string
  label: string
  icon: Component
  roles: UserRole[]
}

const staffRoles: UserRole[] = ['doctor', 'admin', 'super_admin']

const route = useRoute()
const router = useRouter()
const { state: authState, signOut } = useAuthSession()

const navItems: AdminNavItem[] = [
  { path: '/admin/dashboard', label: '数据看板', icon: LayoutDashboard, roles: staffRoles },
  { path: '/admin/patients', label: '用户管理', icon: Users, roles: staffRoles },
  { path: '/admin/assessment-task-publishing', label: '发布测评任务', icon: Send, roles: staffRoles },
  { path: '/admin/intervention-task-publishing', label: '发布干预任务', icon: HeartPulse, roles: staffRoles },
  { path: '/admin/brain-intervention-reports', label: '训练报告', icon: FileText, roles: staffRoles },
  { path: '/admin/scale-assessments', label: '量表测评', icon: ClipboardList, roles: staffRoles },
  { path: '/admin/neuropsych-assessments', label: '神经心理测评', icon: Brain, roles: staffRoles },
  { path: '/admin/knowledge', label: '知识库', icon: BookOpen, roles: staffRoles },
  { path: '/admin/alerts', label: '预警消息', icon: AlertTriangle, roles: staffRoles },
  { path: '/admin/departments', label: '部门管理', icon: Building2, roles: ['super_admin'] },
]

const displayName = computed(() => authState.profile?.full_name || authState.profile?.username || '')
const roleName = computed(() => (authState.profile?.role === 'super_admin' ? '超级管理员' : '管理员'))
const visibleNavItems = computed(() => {
  const role = authState.profile?.role
  return navItems.filter((item) => role && item.roles.includes(role))
})

const handleLogout = async () => {
  await signOut()
  router.push('/login')
}
</script>

<template>
  <div class="flex min-h-screen bg-background">
    <aside class="sticky left-0 top-0 z-50 hidden h-screen w-64 flex-col border-r border-slate-200 bg-slate-50 transition-all duration-300 md:flex dark:border-slate-800 dark:bg-slate-950">
      <div class="flex h-full flex-col">
        <div class="flex h-16 items-center border-b border-slate-200 px-6 dark:border-slate-800">
          <h1 class="text-lg font-semibold text-slate-900 dark:text-slate-100">管理员后台</h1>
        </div>

        <nav class="flex-1 space-y-2 overflow-y-auto p-4">
          <RouterLink
            v-for="item in visibleNavItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 rounded-lg px-4 py-3 transition-colors"
            :class="
              route.path === item.path
                ? 'bg-slate-200 text-slate-950 dark:bg-slate-800 dark:text-white'
                : 'text-slate-700 hover:bg-slate-200/60 dark:text-slate-200 dark:hover:bg-slate-800/60'
            "
          >
            <component :is="item.icon" class="h-5 w-5" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="border-t border-slate-200 p-4 dark:border-slate-800">
          <div class="mb-3 rounded-lg bg-slate-200 px-4 py-2 dark:bg-slate-800">
            <p class="text-sm font-medium text-slate-900 dark:text-slate-100">{{ displayName }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ roleName }}</p>
          </div>
          <button
            class="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-transparent px-4 text-sm font-medium text-slate-800 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-100 dark:hover:bg-slate-800"
            type="button"
            @click="handleLogout"
          >
            <LogOut class="h-4 w-4" />
            退出登录
          </button>
        </div>
      </div>
    </aside>

    <div class="flex min-h-screen flex-1 flex-col">
      <header class="sticky top-0 z-30 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80">
        <div class="flex h-full items-center justify-between px-4 md:px-8">
          <h1 class="text-xl font-bold md:hidden">初心 管理员后台</h1>
          <div class="hidden md:block" />
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 md:hidden dark:bg-slate-800">
              <span class="text-xs font-medium">{{ displayName }}</span>
              <button class="grid h-6 w-6 place-items-center rounded-md hover:bg-slate-200 dark:hover:bg-slate-700" type="button" @click="handleLogout">
                <LogOut class="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main class="flex-1 overflow-x-hidden p-4 pb-24 md:p-8 md:pb-8">
        <div class="mx-auto max-w-7xl">
          <RouterView />
        </div>
      </main>

      <nav class="fixed inset-x-0 bottom-0 z-50 flex h-16 items-center justify-around border-t border-slate-200 bg-white px-2 shadow-[0_-4px_10px_rgba(0,0,0,0.05)] md:hidden dark:border-slate-800 dark:bg-slate-900">
        <RouterLink
          v-for="item in visibleNavItems"
          :key="item.path"
          :to="item.path"
          class="relative flex h-full flex-1 flex-col items-center justify-center transition-colors"
          :class="route.path === item.path ? 'text-primary' : 'text-slate-500 dark:text-slate-400'"
        >
          <component :is="item.icon" class="mb-1 h-6 w-6" />
          <span class="text-[10px] font-medium leading-none">{{ item.label }}</span>
          <span v-if="route.path === item.path" class="absolute -top-px h-0.5 w-12 rounded-full bg-primary" />
        </RouterLink>
      </nav>
    </div>
  </div>
</template>
