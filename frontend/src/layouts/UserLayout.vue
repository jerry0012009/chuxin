<script setup lang="ts">
import { Activity, Brain, BrainCircuit, ClipboardList, Heart, HeartPulse, Home, ListChecks, NotebookPen, User } from 'lucide-vue-next'
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAppState } from '@/composables/useAppState'
import ServiceShell from '@/components/ui/ServiceShell.vue'

const route = useRoute()
const { refreshCurrentAccountProfile } = useAppState()

const navigation = [
  { path: '/', label: '我的工作台', icon: Home },
  { path: '/assessment-tasks', label: '测评任务', icon: ListChecks },
  { path: '/profile/healing-plan', label: '干预计划', icon: HeartPulse },
  { path: '/record', label: '情绪记录', icon: NotebookPen, secondary: true },
  { path: '/scale-assessment', label: '量表测评', icon: ClipboardList, secondary: true },
  { path: '/assessment', label: 'AI 多模态评估', icon: Activity, secondary: true },
  { path: '/neuropsych-assessment', label: '神经心理', icon: Brain, secondary: true },
  { path: '/brain-intervention', label: '脑机调控', icon: BrainCircuit, secondary: true },
  { path: '/healing', label: '身心练习', icon: Heart, secondary: true },
  { path: '/profile', label: '个人中心', icon: User, secondary: true },
]

const pageTitle = computed(() => {
  if (route.path.startsWith('/record')) return '情绪记录'
  if (route.path.startsWith('/brain-intervention/reports')) return '脑机训练报告'
  if (route.path.startsWith('/neuropsych-assessment/report')) return '神经心理报告'
  return navigation.filter(({ path }) => route.path === path || route.path.startsWith(`${path}/`)).sort((a, b) => b.path.length - a.path.length)[0]?.label
})
const hero = computed(() => {
  if (route.path === '/' || route.path.startsWith('/assessment-tasks') || route.path === '/record' || route.path === '/profile/healing-plan' || route.path === '/scale-assessment' && !route.query.returnTo) return undefined
  return 'quiet'
})

onMounted(() => {
  void refreshCurrentAccountProfile().catch(() => {
    // The account pages handle their own profile errors.
  })
})
</script>

<template>
  <ServiceShell :navigation="navigation" area="用户服务" :title="pageTitle" :hero="hero" home="/">
    <RouterView />
  </ServiceShell>
</template>
