<script setup lang="ts">
import { Activity, ArrowRight, Brain, BrainCircuit, CalendarDays, ClipboardList, FileClock, Gamepad2, Heart, ListChecks, NotebookPen } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ServiceHero from '@/components/ui/ServiceHero.vue'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import { assessmentItemName, nextAssessmentItem } from '@/lib/assessment-display'
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
const nextItem = computed(() => nextAssessmentItem(current.value?.items || []))
const continuing = computed(() => current.value?.status === 'in_progress' || current.value?.items?.some((item) => item.status === 'in_progress' || item.status === 'completed'))
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
  <div class="workbench">
    <ServiceHero variant="full" title="我的工作台" eyebrow="高原身心健康研究">
      <p v-if="auth.user" class="workbench-greeting">您好，{{ displayName }}</p>
      <p class="workbench-date"><CalendarDays aria-hidden="true" />{{ todayLabel }}</p>
    </ServiceHero>

    <div class="service-width workbench-body">
    <div v-if="!auth.user" class="service-card work-card flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm">请登录后查看个人事项。</p>
      <RouterLink to="/login" class="service-button">账号登录 <ArrowRight aria-hidden="true" /></RouterLink>
    </div>
    <p v-if="loading" class="service-muted text-sm" role="status">正在加载个人事项…</p>
    <div v-if="failed.length" class="service-card flex flex-wrap items-center justify-between gap-3 p-4 text-sm" role="alert">
      <p>{{ failed.join('、') }}加载失败。</p><button class="service-button service-outline" type="button" @click="load">重试</button>
    </div>

    <section v-if="auth.user" class="work-grid" aria-label="个人事项">
        <article class="service-card service-card-highlight work-card work-primary" data-testid="work-current">
          <header class="work-card-heading"><span class="service-icon"><ListChecks aria-hidden="true" /></span><h2>当前测评</h2>
            <ServiceStatus v-if="current" :tone="continuing ? 'active' : 'idle'" class="work-task-status">{{ continuing ? '进行中' : '待开始' }}</ServiceStatus>
          </header>
          <template v-if="current">
            <p class="work-task-name">{{ current.batch_title || '测评任务' }}</p>
            <p class="service-muted text-sm" v-if="required.length">已完成 <strong>{{ done }} / {{ required.length }} 项</strong></p>
            <p class="service-muted break-words text-sm" v-if="nextItem">下一步：<strong>{{ assessmentItemName(nextItem) }}</strong></p>
          </template>
          <p v-else-if="!loading && !failed.includes('测评任务')" class="service-muted mt-auto text-sm">暂无待办测评。</p>
          <RouterLink :to="current ? `/assessment-tasks/${current.id}` : '/assessment-tasks'" class="service-button work-continue" data-testid="work-current-link">{{ nextItem ? (continuing ? '继续测评' : '开始测评') : '查看测评任务' }} <ArrowRight aria-hidden="true" /></RouterLink>
        </article>

        <article class="service-card work-card work-secondary" data-testid="work-intervention">
          <header class="work-card-heading"><span class="service-icon"><Heart aria-hidden="true" /></span><h2>今日干预</h2></header>
          <template v-if="today?.tasks.length">
            <p class="service-muted text-sm">已完成 <strong>{{ today.summary.completed }} / {{ today.summary.total }} 项</strong></p>
            <ul class="work-list">
              <li v-for="task in today.tasks.slice(0, 3)" :key="task.id" class="work-intervention-row">
                <RouterLink :to="task.navigation_path || task.route_path || '/healing'" class="service-link break-words">{{ task.title }}</RouterLink>
                <ServiceStatus :tone="task.status === 'completed' ? 'done' : task.status === 'in_progress' ? 'active' : 'idle'">{{ task.status === 'completed' ? '已完成' : task.status === 'in_progress' ? '进行中' : task.status === 'expired' ? '已过期' : '待完成' }}</ServiceStatus>
              </li>
            </ul>
          </template>
          <p v-else-if="!loading && !failed.includes('今日干预')" class="service-muted text-sm">今日暂无干预任务。</p>
          <RouterLink to="/profile/healing-plan" class="work-action service-link">查看干预计划 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>

        <article class="service-card work-card work-secondary" data-testid="work-records">
          <header class="work-card-heading"><span class="service-icon"><FileClock aria-hidden="true" /></span><h2>测评记录</h2></header>
          <ul v-if="records.length" class="work-list">
            <li v-for="record in records" :key="record.id" class="work-record-row">
              <RouterLink :to="{ path: '/scale-assessment', query: { recordId: record.id } }" class="service-link">{{ record.survey_title || record.survey?.title || '量表测评报告' }}</RouterLink>
              <p class="service-muted mt-1 text-xs">{{ dateLabel(record.completed_at || record.sent_at) }}</p>
            </li>
          </ul>
          <p v-else-if="!loading && !failed.includes('测评记录')" class="service-muted text-sm">暂无已完成的量表测评。</p>
          <RouterLink :to="{ path: '/scale-assessment', query: { tab: 'completed' } }" class="work-action service-link">查看量表记录 <ArrowRight aria-hidden="true" /></RouterLink>
        </article>
    </section>

    <section aria-labelledby="work-services">
      <h2 id="work-services" class="work-services-title">常用服务</h2>
      <div class="work-service-grid">
        <RouterLink v-for="link in links" :key="link.title" :to="link.to" :data-testid="link.test" class="service-card work-service">
          <component :is="link.icon" class="work-service-icon" aria-hidden="true" /><span>{{ link.title }}</span><ArrowRight class="work-service-arrow" aria-hidden="true" />
        </RouterLink>
      </div>
    </section>
    </div>
  </div>
</template>

<style scoped>
.workbench-greeting { margin-top: 12px; color: #514345; font-size: 15px; overflow-wrap: anywhere; }
.workbench-date { display: flex; align-items: center; gap: 6px; margin-top: 12px; color: var(--service-muted); font-size: 13px; }
.workbench-date svg, .work-action svg { width: 16px; height: 16px; flex-shrink: 0; }
.workbench-body { display: grid; gap: 26px; padding-block: 24px 36px; }
.work-grid { display: grid; grid-template-columns: minmax(0, 1.45fr) repeat(2, minmax(0, 1fr)); gap: 14px; }
.work-card { min-width: 0; padding: 20px; }
.work-primary, .work-secondary { display: flex; flex-direction: column; gap: 12px; }
.work-card-heading { display: flex; align-items: center; gap: 9px; }
.work-card-heading h2 { font-size: 16px; font-weight: 720; }
.work-card-heading .service-icon { width: 34px; height: 34px; flex-basis: 34px; }
.work-card-heading .service-icon svg { width: 18px; height: 18px; }
.work-task-status { margin-left: auto; }
.work-task-name { margin-block: 2px; font-size: 22px; line-height: 1.4; font-weight: 720; overflow-wrap: anywhere; }
.work-continue { margin-top: auto; align-self: flex-start; min-height: 44px; padding-inline: 16px; }
.work-list { font-size: 14px; }
.work-list li + li { border-top: 1px solid #efe8df; }
.work-intervention-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 6px; min-height: 36px; }
.work-intervention-row a { padding-block: 7px; }
.work-record-row { padding-block: 6px; overflow-wrap: anywhere; }
.work-action { display: inline-flex; gap: 6px; align-items: center; align-self: flex-start; min-height: 40px; margin-top: auto; font-size: 14px; }
.work-services-title { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; font-size: 19px; font-weight: 720; }
.work-services-title::after { content: ''; height: 1px; flex: 1; background: var(--service-border); }
.work-service-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.work-service { display: flex; align-items: center; gap: 8px; min-height: 48px; min-width: 0; padding: 8px 12px; font-size: 14px; }
.work-service:hover { color: var(--service-red); border-color: #bf8b8e; }
.work-service-icon { width: 19px; height: 19px; flex-shrink: 0; color: var(--service-red); stroke-width: 1.7; }
.work-service-arrow { width: 14px; height: 14px; flex-shrink: 0; margin-left: auto; color: var(--service-muted); }
@media (max-width: 900px) { .work-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .work-primary { grid-column: 1 / -1; } }
@media (max-width: 640px) {
  .workbench-body { padding-block: 16px 28px; gap: 22px; }
  .work-grid { grid-template-columns: minmax(0, 1fr); gap: 10px; }
  .work-card { padding: 16px; }
  .work-task-name { font-size: 20px; }
  .work-service-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .work-service-arrow { display: none; }
}
</style>
