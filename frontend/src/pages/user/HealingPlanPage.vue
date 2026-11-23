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
  mood: { label: '心情日记', icon: NotebookPen, tone: 'bg-amber-50 text-amber-700' },
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
    errorMessage.value = error instanceof Error ? error.message : '加载疗愈计划失败'
  } finally {
    loading.value = false
  }
}

const switchPlan = (offset: number) => {
  if (planCount.value <= 1) return
  selectedPlanIndex.value = (selectedPlanIndex.value + offset + planCount.value) % planCount.value
}

const selectPlan = (index: number) => {
  selectedPlanIndex.value = index
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
  <div class="bg-background pb-12">
    <div class="sticky top-0 z-30 flex items-center justify-between border-b border-slate-100 bg-white/85 px-4 py-4 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/85">
      <div class="flex items-center gap-4">
        <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800" @click="router.back()">
          <ChevronLeft class="h-6 w-6 text-slate-600 dark:text-slate-400" />
        </button>
        <h1 class="text-lg font-bold text-slate-900 dark:text-white">疗愈计划</h1>
      </div>
      <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800" type="button" @click="loadPlan">
        <RefreshCw class="h-5 w-5 text-slate-500" />
      </button>
    </div>

    <main class="mx-auto max-w-5xl space-y-6 px-4 pt-6">
      <div v-if="loading" class="rounded-[28px] bg-white p-10 text-center text-slate-500 shadow-sm dark:bg-slate-900">
        <Loader2 class="mx-auto h-6 w-6 animate-spin" />
        <p class="mt-3 text-sm">正在加载管理员发布的疗愈计划...</p>
      </div>

      <div v-else-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">
        {{ errorMessage }}
      </div>

      <template v-else>
        <section v-if="!plans.length" class="overflow-hidden rounded-[28px] border border-slate-100 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div class="grid h-14 w-14 place-items-center rounded-2xl bg-emerald-50 text-emerald-700">
            <HeartPulse class="h-7 w-7" />
          </div>
          <h2 class="mt-5 text-2xl font-black text-slate-900 dark:text-white">暂无管理员发布的疗愈计划</h2>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-500">你仍可进入疗愈页面自由练习冥想、记录心情或阅读知识内容。管理员发布干预任务后，这里会显示每日任务、计划进度和日历小结。</p>
          <button class="mt-5 rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="router.push('/healing')">进入疗愈</button>
        </section>

        <section v-else class="service-card service-card-highlight p-4 sm:p-6">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div class="min-w-0 flex-1">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div class="inline-flex w-fit items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-200">
                  <HeartPulse class="h-4 w-4" />
                  {{ riskText(primaryPlan?.risk_level) }}
                </div>
                <div v-if="planCount > 1" class="inline-flex w-fit items-center gap-2 rounded-full bg-white/80 p-1 shadow-sm ring-1 ring-emerald-100 dark:bg-slate-900/70 dark:ring-slate-800">
                  <button class="grid h-8 w-8 place-items-center rounded-full text-slate-500 transition hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-slate-800 dark:hover:text-emerald-200" type="button" aria-label="查看上一个疗愈计划" @click="switchPlan(-1)">
                    <ChevronLeft class="h-4 w-4" />
                  </button>
                  <span class="min-w-16 text-center text-xs font-black text-slate-600 dark:text-slate-300">计划 {{ selectedPlanIndex + 1 }} / {{ planCount }}</span>
                  <button class="grid h-8 w-8 place-items-center rounded-full text-slate-500 transition hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-slate-800 dark:hover:text-emerald-200" type="button" aria-label="查看下一个疗愈计划" @click="switchPlan(1)">
                    <ChevronRight class="h-4 w-4" />
                  </button>
                </div>
              </div>
              <h2 class="mt-4 text-3xl font-black text-slate-900 dark:text-white">{{ primaryPlan?.batch_title || '当前疗愈计划' }}</h2>
              <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">{{ primaryPlan?.batch_description || '按照管理员发布的干预项目完成每日练习，系统会记录进度并生成小结。' }}</p>
              <div v-if="planCount > 1" class="mt-4 flex flex-wrap gap-2">
                <button
                  v-for="(plan, index) in visiblePlans"
                  :key="plan.id"
                  class="h-2.5 rounded-full transition-all"
                  :class="selectedPlanIndex === Number(index) ? 'w-8 bg-emerald-500' : 'w-2.5 bg-emerald-200 hover:bg-emerald-300 dark:bg-slate-700 dark:hover:bg-slate-600'"
                  type="button"
                  :aria-label="`切换到疗愈计划 ${Number(index) + 1}`"
                  @click="selectPlan(Number(index))"
                />
              </div>
            </div>
            <div class="min-w-64 rounded-3xl bg-white/80 p-5 shadow-sm ring-1 ring-emerald-100 dark:bg-slate-900/70 dark:ring-slate-800">
              <div class="flex items-center justify-between text-sm">
                <span>计划进度</span>
                <span class="font-black">{{ primaryPlan?.completed_days || 0 }} / {{ primaryPlan?.duration_days || 0 }} 天</span>
              </div>
              <div class="mt-3 h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div class="h-full rounded-full bg-primary" :style="{ width: `${progress}%` }" />
              </div>
              <p class="mt-2 text-xs text-slate-500">今日完成 {{ today.summary.completed }} / {{ today.summary.total }}</p>
              <p class="mt-1 text-[11px] text-slate-400">多个计划共享同一项目时，完成一次会同步回写。</p>
            </div>
          </div>
        </section>

        <section class="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.16em] text-emerald-500">TODAY</p>
                <h3 class="mt-1 text-xl font-black text-slate-900 dark:text-white">今日干预</h3>
              </div>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-800">{{ today.summary.completed }} / {{ today.summary.total }}</span>
            </div>

            <div v-if="!todayTasks.length" class="mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500 dark:bg-slate-950">
              今日暂无待完成干预子项目。
            </div>
            <div v-else class="mt-5 grid gap-3">
              <article v-for="task in todayTasks" :key="task.id" class="rounded-[22px] border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                <div class="flex items-center gap-3">
                  <div :class="['grid h-11 w-11 shrink-0 place-items-center rounded-2xl', categoryMeta[task.item_type]?.tone || 'bg-slate-100 text-slate-600']">
                    <component :is="categoryMeta[task.item_type]?.icon || Sparkles" class="h-5 w-5" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <p class="font-black text-slate-900 dark:text-white">{{ task.title }}</p>
                      <span class="rounded-full px-2 py-0.5 text-[10px] font-bold" :class="task.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-white text-slate-500 dark:bg-slate-900'">{{ statusText(task.status) }}</span>
                    </div>
                    <p class="mt-1 text-xs text-slate-500">{{ categoryMeta[task.item_type]?.label }} · {{ task.completion_mode === 'diary_once' ? '保存日记后完成' : `${task.duration_sec || 10} 秒后可完成` }}</p>
                  </div>
                  <button class="rounded-xl bg-slate-900 px-3 py-2 text-xs font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="openTask(task)">
                    {{ task.status === 'completed' ? '再练习' : '去完成' }}
                  </button>
                </div>
              </article>
            </div>
          </div>

          <div class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div class="flex items-center gap-3">
              <div class="grid h-10 w-10 place-items-center rounded-2xl bg-cyan-50 text-cyan-700">
                <Target class="h-5 w-5" />
              </div>
              <div>
                <h3 class="text-lg font-black text-slate-900 dark:text-white">计划内容</h3>
                <p class="text-xs text-slate-500">多个计划并存时，今日任务会自动合并展示。</p>
              </div>
            </div>
            <div class="mt-5 space-y-4">
              <article v-for="plan in plans" :key="plan.id" class="rounded-[22px] bg-slate-50 p-4 dark:bg-slate-950">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="font-black text-slate-900 dark:text-white">{{ plan.batch_title }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ plan.start_date }} 至 {{ plan.end_date }} · {{ statusText(plan.status) }}</p>
                  </div>
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-900">{{ plan.items?.length || 0 }} 项</span>
                </div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span v-for="item in plan.items || []" :key="item.id" class="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-900">
                    {{ item.title }}
                  </span>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div class="flex items-center gap-3">
            <div class="grid h-10 w-10 place-items-center rounded-2xl bg-amber-50 text-amber-700">
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
              class="rounded-2xl border p-4 text-left transition hover:border-emerald-200 hover:bg-emerald-50 dark:hover:bg-emerald-950/20"
              :class="selectedDate === item.summary_date ? 'border-emerald-300 bg-emerald-50 dark:bg-emerald-950/20' : 'border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-950'"
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
                <span :class="task.status === 'completed' ? 'text-emerald-600' : 'text-slate-400'">{{ statusText(task.status) }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>
