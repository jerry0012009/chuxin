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
  Send,
  Users,
} from 'lucide-vue-next'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthSession } from '@/composables/useAuthSession'
import ServiceShell from '@/components/ui/ServiceShell.vue'
import type { Component } from 'vue'
import type { UserRole } from '@/types'

type AdminNavItem = {
  path: string
  label: string
  icon: Component
  roles: UserRole[]
  secondary?: boolean
}

const staffRoles: UserRole[] = ['doctor', 'admin', 'super_admin']

const { state: authState } = useAuthSession()

const navItems: AdminNavItem[] = [
  { path: '/admin/dashboard', label: '数据看板', icon: LayoutDashboard, roles: staffRoles },
  { path: '/admin/assessment-task-publishing', label: '发布测评任务', icon: Send, roles: staffRoles },
  { path: '/admin/intervention-task-publishing', label: '发布干预任务', icon: HeartPulse, roles: staffRoles },
  { path: '/admin/alerts', label: '预警消息', icon: AlertTriangle, roles: staffRoles },
  { path: '/admin/patients', label: '参与者管理', icon: Users, roles: staffRoles, secondary: true },
  { path: '/admin/brain-intervention-reports', label: '训练报告', icon: FileText, roles: staffRoles, secondary: true },
  { path: '/admin/scale-assessments', label: '量表测评', icon: ClipboardList, roles: staffRoles, secondary: true },
  { path: '/admin/neuropsych-assessments', label: '神经心理测评', icon: Brain, roles: staffRoles, secondary: true },
  { path: '/admin/knowledge', label: '知识库', icon: BookOpen, roles: staffRoles, secondary: true },
  { path: '/admin/departments', label: '部门管理', icon: Building2, roles: ['super_admin'], secondary: true },
]

const visibleNavItems = computed(() => {
  const role = authState.profile?.role
  return navItems.filter((item) => role && item.roles.includes(role))
})

</script>

<template>
  <ServiceShell :navigation="visibleNavItems" area="管理员后台" home="/admin/dashboard">
    <div class="service-width min-w-0 py-5 sm:py-7">
      <RouterView />
    </div>
  </ServiceShell>
</template>
