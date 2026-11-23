<script setup lang="ts">
import { Activity, ArrowRight, Brain, BrainCircuit, CalendarDays, ClipboardList, FileClock, Gamepad2, Heart, ListChecks, NotebookPen } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthSession } from '@/composables/useAuthSession'
import { getMyAssessmentPublishTasks, getMyInterventionTodayTasks, getMyScaleRecords } from '@/db/api'
import type { AssessmentPublishAssignee, InterventionTodayResponse, ScaleDistributionRecord } from '@/types'

const { state: auth } = useAuthSession()
const tasks = ref<AssessmentPublishAssignee[]>([])
const today = ref<InterventionTodayResponse | null>(null)
const records = ref<ScaleDistributionRecord[]>([])
const loading = ref(false)
const failed = ref<string[]>([])
const current = computed(() => tasks.value.find((task) => ['pending', 'in_progress'].includes(task.status)))
const required = computed(() => (current.value?.items || []).filter((item) => item.required !== false))
const done = computed(() => required.value.filter((item) => ['completed', 'unsupported'].includes(item.status)).length)
const displayName = computed(() => auth.profile?.full_name || auth.profile?.username || '用户')
const todayLabel = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full' }).format(new Date())
const dateLabel = (date?: string | null) => date ? new Date(date).toLocaleDateString('zh-CN') : ''
const links = [
  { title: '量表测评', to: '/scale-assessment', icon: ClipboardList },
  { title: 'AI多模态评估', to: '/assessment', icon: Activity, test: 'home-feature-assessment' },
  { title: '神经心理', to: '/neuropsych-assessment', icon: Brain },
  { title: '脑机调控', to: '/brain-intervention', icon: BrainCircuit },
  { title: '情绪记录', to: '/record', icon: NotebookPen, test: 'home-feature-record' },
  { title: '放松疗愈', to: '/healing', icon: Heart, test: 'home-feature-healing' },
  { title: '疗愈游戏', to: { path: '/healing', state: { activeTab: 'game' } }, icon: Gamepad2, test: 'home-game-card' },
]

async function load() {
  if (!auth.user) return
  loading.value = true
  failed.value = []
  await Promise.all([
    getMyAssessmentPublishTasks().then((result) => { tasks.value = result }).catch(() => { failed.value.push('测评任务') }),
    getMyInterventionTodayTasks().then((result) => { today.value = result }).catch(() => { failed.value.push('今日干预') }),
    getMyScaleRecords().then((result) => {
      records.value = result.filter((record) => record.status === 'completed' && record.calc_status === 'done')
        .sort((a, b) => (b.completed_at || b.sent_at).localeCompare(a.completed_at || a.sent_at)).slice(0, 3)
    }).catch(() => { failed.value.push('测评记录') }),
  ])
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div class="service-width space-y-7 py-6 sm:py-9">
    <header class="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold sm:text-[30px]">我的工作台</h1>
        <p v-if="auth.user" class="service-muted mt-2 text-sm">您好，{{ displayName }}</p>
      </div>
      <p class="service-muted inline-flex items-center gap-2 text-sm"><CalendarDays class="h-4 w-4" aria-hidden="true" />{{ todayLabel }}</p>
    </header>

    <div v-if="!auth.user" class="service-card flex flex-wrap items-center justify-between gap-3 p-5">
      <p class="text-sm">请登录后查看个人事项。</p>
      <RouterLink to="/login" class="service-button">账号登录 <ArrowRight aria-hidden="true" /></RouterLink>
    </div>
    <p v-if="loading" class="service-muted text-sm" role="status">正在加载个人事项…</p>
    <div v-if="failed.length" class="service-card flex flex-wrap items-center justify-between gap-3 p-4 text-sm" role="alert">
      <p>{{ failed.join('、') }}加载失败。</p><button class="service-button service-outline" type="button" @click="load">重试</button>
    </div>

    <section v-if="auth.user" aria-labelledby="work-overview">
      <h2 id="work-overview" class="service-sec-title mb-3">个人事项</h2>
      <div class="grid gap-3 md:grid-cols-3">
        <article class="service-card flex min-w-0 flex-col gap-3 p-4 sm:p-5" data-testid="work-current">
          <header class="flex items-center gap-2"><span class="service-icon"><ListChecks aria-hidden="true" /></span><h3 class="font-bold">当前测评</h3></header>
          <template v-if="current">
            <p class="font-semibold leading-6">{{ current.batch_title || '测评任务' }}</p>
            <div class="mt-auto space-y-2"><p class="service-muted text-sm">办理进度 <strong>{{ done }} / {{ required.length }} 项</strong></p>
              <progress v-if="required.length" class="service-progress block" :value="done" :max="required.length" aria-label="测评任务完成进度" />
            </div>
          </template>
          <p v-else-if="!loading && !failed.includes('测评任务')" class="service-muted mt-auto text-sm">暂无待办测评。</p>
          <RouterLink :to="current ? `/assessment-tasks/${current.id}` : '/assessment-tasks'" class="service-button mt-1 self-start" data-testid="work-current-link">{{ current ? '查看任务详情' : '查看测评任务' }} <ArrowRight aria-hidden="true" /></RouterLink>
        </article>

        <article class="service-card flex min-w-0 flex-col gap-3 p-4 sm:p-5" data-testid="work-intervention">
          <header class="flex items-center gap-2"><span class="service-icon"><Heart aria-hidden="true" /></span><h3 class="font-bold">今日干预</h3></header>
          <template v-if="today?.tasks.length">
            <p class="service-muted text-sm">已完成 <strong>{{ today.summary.completed }} / {{ today.summary.total }} 项</strong></p>
            <ul class="space-y-2">
              <li v-for="task in today.tasks.slice(0, 3)" :key="task.id" class="flex items-center justify-between gap-2 text-sm">
                <RouterLink :to="task.navigation_path || task.route_path || '/healing'" class="service-link break-words">{{ task.title }}</RouterLink>
                <span class="service-status" :class="task.status === 'completed' ? 'service-status-done' : 'service-status-idle'">{{ task.status === 'completed' ? '已完成' : task.status === 'in_progress' ? '进行中' : task.status === 'expired' ? '已过期' : '待完成' }}</span>
              </li>
            </ul>
          </template>
          <p v-else-if="!loading && !failed.includes('今日干预')" class="service-muted text-sm">今日暂无干预任务。</p>
          <RouterLink to="/profile/healing-plan" class="service-button service-outline mt-auto self-start">查看疗愈计划 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>

        <article class="service-card flex min-w-0 flex-col gap-3 p-4 sm:p-5" data-testid="work-records">
          <header class="flex items-center gap-2"><span class="service-icon"><FileClock aria-hidden="true" /></span><h3 class="font-bold">测评记录</h3></header>
          <ul v-if="records.length" class="divide-y text-sm">
            <li v-for="record in records" :key="record.id" class="py-2 first:pt-0">
              <RouterLink :to="{ path: '/scale-assessment', query: { recordId: record.id } }" class="service-link">{{ record.survey_title || record.survey?.title || '量表测评报告' }}</RouterLink>
              <p class="service-muted mt-1 text-xs">{{ dateLabel(record.completed_at || record.sent_at) }}</p>
            </li>
          </ul>
          <p v-else-if="!loading && !failed.includes('测评记录')" class="service-muted text-sm">暂无已完成的量表测评。</p>
          <RouterLink :to="{ path: '/scale-assessment', query: { tab: 'completed' } }" class="service-button service-outline mt-auto self-start">查看量表记录 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>
      </div>
    </section>

    <section aria-labelledby="work-services">
      <h2 id="work-services" class="service-sec-title mb-3">常用服务</h2>
      <div class="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
        <RouterLink v-for="link in links" :key="link.title" :to="link.to" :data-testid="link.test" class="service-card flex min-h-[58px] min-w-0 items-center gap-2 px-3 py-2 text-sm font-medium transition hover:border-[var(--service-red)] hover:text-[var(--service-red)]">
          <component :is="link.icon" class="h-5 w-5 shrink-0 text-[var(--service-red)]" aria-hidden="true" />{{ link.title }}<ArrowRight class="ml-auto hidden h-4 w-4 shrink-0 sm:block" aria-hidden="true" />
        </RouterLink>
      </div>
    </section>
  </div>
</template>
