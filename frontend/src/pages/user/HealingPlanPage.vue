<script setup lang="ts">
import {
  Brain,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  Gamepad2,
  HeartPulse,
  Loader2,
  Music,
  NotebookPen,
  RefreshCw,
  Sparkles,
  Target,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { InterventionDailySummary, InterventionTodayTask } from '@/types'
import { getMyInterventionCalendarDate, getMyInterventionPlan } from '@/db/api'

const router = useRouter()
const loading = ref(true)
const errorMessage = ref('')
const planData = ref<any | null>(null)
const selectedDate = ref('')
const dateDetail = ref<any | null>(null)
const selectedPlanIndex = ref(0)

const plans = computed(() => planData.value?.plans || [])
const today = computed(() => planData.value?.today || { tasks: [], summary: { total: 0, completed: 0, pending: 0 } })
const todayTasks = computed<InterventionTodayTask[]>(() => today.value.tasks || [])
const calendar = computed<InterventionDailySummary[]>(() => planData.value?.calendar || [])
const activePlans = computed(() => plans.value.filter((item: any) => ['pending', 'in_progress'].includes(item.status)))
const visiblePlans = computed(() => activePlans.value.length ? activePlans.value : plans.value)
const primaryPlan = computed(() => visiblePlans.value[selectedPlanIndex.value] || visiblePlans.value[0] || null)
const planCount = computed(() => visiblePlans.value.length)
const progress = computed(() => {
  const plan = primaryPlan.value
  if (!plan) return 0
  return Math.min(100, Math.round(((plan.completed_days || 0) / Math.max(1, plan.duration_days || 1)) * 100))
})

const categoryMeta: Record<string, { label: string; icon: any; tone: string }> = {
  mood: { label: '心情日记', icon: NotebookPen, tone: 'bg-muted text-primary' },
  meditation: { label: '冥想练习', icon: Music, tone: 'bg-cyan-50 text-cyan-700' },
  knowledge: { label: '知识学习', icon: FileText, tone: 'bg-emerald-50 text-emerald-700' },
  game: { label: '游戏训练', icon: Gamepad2, tone: 'bg-orange-50 text-orange-700' },
  brain_intervention: { label: '脑机干预', icon: Brain, tone: 'bg-slate-900 text-white' },
}

const statusText = (status?: string) => {
  if (status === 'completed') return '已完成'
  if (status === 'in_progress') return '进行中'
  if (status === 'expired') return '已结束'
  if (status === 'cancelled') return '已取消'
  return '待完成'
}

const riskText = (risk?: string | null) => {
  if (risk === 'high') return '高风险强化'
  if (risk === 'middle') return '中风险调节'
  if (risk === 'low') return '低风险维护'
  return '手动计划'
}

const loadPlan = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    planData.value = await getMyInterventionPlan()
    selectedPlanIndex.value = 0
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载干预计划失败'
  } finally {
    loading.value = false
  }
}

const openTask = (task: InterventionTodayTask) => {
  void router.push(task.navigation_path || task.route_path || '/healing')
}

const openDate = async (date: string) => {
  selectedDate.value = date
  dateDetail.value = await getMyInterventionCalendarDate(date).catch(() => null)
}

onMounted(loadPlan)
</script>

<template>
  <div class="service-width py-5 sm:py-7 space-y-7">
    <div class="flex items-center justify-between gap-3">
      <h1 class="service-sec-title">今日任务</h1>
      <div class="flex gap-2"><button class="service-button service-outline" type="button" @click="router.back()"><ChevronLeft aria-hidden="true" />返回</button>
      <button class="service-button service-outline" type="button" @click="loadPlan"><RefreshCw aria-hidden="true" />刷新</button></div>
    </div>
    <p v-if="loading" role="status">正在加载干预计划…</p>
    <p v-else-if="errorMessage" role="alert" class="text-primary">{{ errorMessage }}</p>
    <template v-else>
      <section aria-label="今日干预">
        <p class="mb-3 font-semibold">今日已完成 {{ today.summary.completed }} / {{ today.summary.total }} 项</p>
        <p v-if="!todayTasks.length" class="service-muted py-4">今日暂无干预任务。</p>
        <div v-else>
          <div class="service-list-row service-list-head" aria-hidden="true"><span>任务</span><span>完成要求</span><span>状态</span><span>操作</span></div>
          <ul><li v-for="task in todayTasks" :key="task.id" class="service-list-row text-sm">
            <div class="task-name flex min-w-0 items-center gap-2"><span class="service-icon"><component :is="categoryMeta[task.item_type]?.icon || Sparkles" aria-hidden="true" /></span><div class="min-w-0"><strong class="break-words">{{ task.title }}</strong><p class="service-muted text-xs">{{ categoryMeta[task.item_type]?.label }}</p></div></div>
            <span class="task-requirement service-muted"><span class="service-list-label">要求：</span>{{ task.completion_mode === 'diary_once' ? '保存一篇日记' : '练习 ' + (task.duration_sec || 10) + ' 秒' }}</span>
            <span class="task-state service-status" :class="task.status === 'in_progress' ? 'service-status-active' : 'service-status-idle'">{{ statusText(task.status) }}</span>
            <button class="service-button service-outline" type="button" @click="openTask(task)">{{ task.status === 'completed' ? '再练习' : '去完成' }}<ChevronRight aria-hidden="true" /></button>
          </li></ul>
        </div>
      </section>
      <section class="space-y-3 border-t pt-5" aria-label="单个计划进度">
        <h2 class="service-sec-title">我的干预计划</h2>
        <template v-if="primaryPlan">
          <label v-if="planCount > 1" class="flex flex-wrap items-center gap-2 text-sm">选择计划<select v-model.number="selectedPlanIndex" class="max-w-full rounded border bg-white p-2"><option v-for="(plan,index) in visiblePlans" :key="plan.id" :value="Number(index)">{{ plan.batch_title }}</option></select></label>
          <div class="flex flex-wrap items-center gap-3"><h3 class="font-semibold">{{ primaryPlan.batch_title }}</h3><span class="service-status service-status-idle">{{ riskText(primaryPlan.risk_level) }}</span></div>
          <p v-if="primaryPlan.batch_description" class="service-muted text-sm">{{ primaryPlan.batch_description }}</p>
          <p class="text-sm">本计划已完成 {{ primaryPlan.completed_days || 0 }} / {{ primaryPlan.duration_days || 0 }} 天</p>
          <progress class="service-progress block max-w-md" :value="progress" max="100" aria-label="所选计划完成天数占比" />
          <details class="border-b py-3"><summary class="service-link cursor-pointer text-sm">全部计划内容（{{ plans.length }}）</summary>
            <article v-for="plan in plans" :key="plan.id" class="border-t py-3 text-sm"><strong>{{ plan.batch_title }}</strong><p class="service-muted">{{ plan.start_date }} 至 {{ plan.end_date }} · {{ statusText(plan.status) }} · {{ plan.items?.length || 0 }} 项</p><ul class="list-inside list-disc"><li v-for="item in plan.items || []" :key="item.id">{{ item.title }}</li></ul></article>
          </details>
        </template>
        <div v-else class="flex flex-wrap items-center gap-3"><p class="service-muted">暂无已发布的计划。</p><button class="service-button service-outline" @click="router.push('/healing')">进入疗愈</button></div>
      </section>
        <section class="border-t pt-5">
          <div class="flex items-center gap-3">
            <div class="grid h-10 w-10 place-items-center rounded-2xl bg-muted text-primary">
              <Calendar class="h-5 w-5" />
            </div>
            <div>
              <h3 class="text-lg font-black text-slate-900 dark:text-white">干预日历小结</h3>
              <p class="text-xs text-slate-500">点击有记录的日期查看当日完成条目。</p>
            </div>
          </div>
          <div class="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <button
              v-for="item in calendar"
              :key="item.id"
              class="rounded-2xl border p-4 text-left transition hover:border-primary hover:bg-muted"
              :class="selectedDate === item.summary_date ? 'border-primary bg-muted' : 'border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-950'"
              type="button"
              @click="openDate(item.summary_date)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="font-black text-slate-900 dark:text-white">{{ item.summary_date.slice(5) }}</span>
                <span class="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-slate-900">{{ item.completed_count }}/{{ item.required_count }}</span>
              </div>
              <p class="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{{ item.summary_text }}</p>
            </button>
          </div>
          <div v-if="selectedDate && dateDetail" class="mt-5 rounded-[24px] bg-slate-50 p-4 dark:bg-slate-950">
            <p class="font-black text-slate-900 dark:text-white">{{ selectedDate }} 完成明细</p>
            <div class="mt-3 grid gap-2">
              <div v-for="task in dateDetail.tasks || []" :key="task.id" class="flex items-center justify-between rounded-xl bg-white px-3 py-2 text-sm dark:bg-slate-900">
                <span>{{ task.title }}</span>
                <span :class="task.status === 'completed' ? 'text-primary' : 'text-slate-400'">{{ statusText(task.status) }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

  </div>
</template>
