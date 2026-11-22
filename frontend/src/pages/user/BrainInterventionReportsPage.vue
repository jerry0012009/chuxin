<script setup lang="ts">
import { Activity, BrainCircuit, ChevronLeft, Loader2, Sparkles, TrendingUp } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMyBrainInterventionReport, getMyBrainInterventionReports } from '@/db/api'
import type { BrainInterventionReport } from '@/types'

const route = useRoute()
const router = useRouter()
const reports = ref<BrainInterventionReport[]>([])
const selectedReport = ref<BrainInterventionReport | null>(null)
const loading = ref(false)
const errorMessage = ref('')

const reportId = computed(() => String(route.params.reportId || ''))
const displayReport = computed(() => selectedReport.value || reports.value[0] || null)
const trendValues = computed(() => {
  const curve = displayReport.value?.curve_json || {}
  const values = Array.isArray(curve.values) ? curve.values : []
  return values.map((item) => Number(item)).filter((item) => Number.isFinite(item))
})
const trendPoints = computed(() => polylinePoints(trendValues.value))
const isMeditationReport = computed(() => displayReport.value?.task_type === 'meditation_biosignal_monitor')
const meditationMetrics = computed(() => {
  const metrics = displayReport.value?.metrics_json || {}
  return (metrics.averages || {}) as Record<string, number>
})
const meditationVideo = computed(() => {
  const metrics = displayReport.value?.metrics_json || {}
  const config = displayReport.value?.config_json || {}
  return {
    id: metrics.videoId || config.video?.id || '',
    name: metrics.videoName || config.video?.title || '',
    type: metrics.videoType || config.video?.type || '',
  }
})

const loadReports = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    reports.value = await getMyBrainInterventionReports()
    if (reportId.value) {
      selectedReport.value = await getMyBrainInterventionReport(reportId.value)
    } else {
      selectedReport.value = reports.value[0] || null
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '训练报告加载失败'
  } finally {
    loading.value = false
  }
}

watch(reportId, () => {
  void loadReports()
})

onMounted(loadReports)

const openReport = (report: BrainInterventionReport) => {
  void router.push(`/brain-intervention/reports/${report.id}`)
}

const formatDate = (value?: string | null) => {
  if (!value) return '--'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

const formatNumber = (value?: number | null, suffix = '') => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '--'
  return `${Number(value).toFixed(Math.abs(Number(value)) >= 100 ? 0 : 1)}${suffix}`
}

const metricLabel = (key?: string | null) => {
  if (key === 'meditation_biosignal_monitor') return '脑机交互冥想'
  if (key === 'theta_training') return 'Theta'
  if (key === 'beta_training') return 'Beta'
  if (key === 'smr_training') return 'SMR'
  if (key === 'theta_beta_ratio') return 'Theta/Beta Ratio'
  return 'Alpha'
}

const taskTypeLabel = (taskType?: string) => {
  if (taskType === 'meditation_biosignal_monitor') return '脑机交互冥想'
  if (taskType === 'neurofeedback') return 'Neurofeedback'
  return taskType || '--'
}

const statusText = (status?: string) => {
  if (status === 'interrupted') return '已中断'
  if (status === 'invalid') return '无效'
  return '已完成'
}

function polylinePoints(values: number[]) {
  if (values.length < 2) return ''
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 320
  const height = 96
  const last = values.length - 1
  return values
    .map((value, index) => {
      const x = (index / last) * width
      const y = height - ((value - min) / range) * height
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}
</script>

<template>
  <main class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/40 px-4 py-6 dark:from-slate-950 dark:via-slate-900 dark:to-cyan-950/20">
    <div class="mx-auto max-w-6xl space-y-5">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <button class="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" type="button" @click="router.push('/brain-intervention')">
            <ChevronLeft class="h-4 w-4" />
            返回脑机调控
          </button>
          <h1 class="mt-3 text-2xl font-black text-slate-900 dark:text-white">我的训练报告</h1>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-300">神经反馈训练记录用于回顾训练过程，不作为疾病诊断或疗效承诺。</p>
        </div>
        <div class="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-bold text-cyan-700 shadow-sm dark:bg-slate-900 dark:text-cyan-200">
          <BrainCircuit class="h-5 w-5" />
          {{ reports.length }} 份报告
        </div>
      </div>

      <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>

      <div v-if="loading" class="flex items-center justify-center rounded-3xl bg-white p-12 text-slate-500 dark:bg-slate-900">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" />
        加载训练报告...
      </div>

      <div v-else class="grid gap-5 lg:grid-cols-[320px_1fr]">
        <aside class="space-y-3">
          <button
            v-for="report in reports"
            :key="report.id"
            type="button"
            class="w-full rounded-2xl border p-4 text-left transition"
            :class="displayReport?.id === report.id ? 'border-cyan-300 bg-cyan-50 dark:border-cyan-700 dark:bg-cyan-950/20' : 'border-slate-100 bg-white hover:border-slate-200 dark:border-slate-800 dark:bg-slate-900'"
            @click="openReport(report)"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="truncate text-sm font-black text-slate-900 dark:text-white">{{ report.task_name }}</p>
              <span class="rounded-full bg-emerald-50 px-2 py-1 text-[11px] font-bold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">{{ statusText(report.status) }}</span>
            </div>
            <p class="mt-2 text-xs font-bold text-slate-400">{{ metricLabel(report.protocol_key) }} · {{ formatDate(report.started_at) }}</p>
            <p class="mt-3 text-sm text-slate-500 dark:text-slate-300">{{ report.summary || '训练报告已生成。' }}</p>
          </button>
          <div v-if="reports.length === 0" class="rounded-3xl bg-white p-8 text-center text-sm text-slate-500 dark:bg-slate-900">
            暂无训练报告。完成一次神经反馈训练后会自动生成记录。
          </div>
        </aside>

        <section v-if="displayReport" class="space-y-5">
          <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div class="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-200">
                  <Sparkles class="h-4 w-4" />
                  {{ metricLabel(displayReport.protocol_key) }} 训练记录
                </div>
                <h2 class="mt-4 text-2xl font-black text-slate-900 dark:text-white">{{ displayReport.task_name }}</h2>
                <p class="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-300">{{ displayReport.summary || '训练报告已生成。' }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-bold text-slate-600 dark:bg-slate-950 dark:text-slate-200">
                {{ formatDate(displayReport.started_at) }}
              </div>
            </div>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
              <p class="text-xs font-bold text-slate-400">{{ isMeditationReport ? '平均冥想稳定度' : '平均反馈值' }}</p>
              <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(displayReport.avg_score) }}</p>
            </div>
            <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
              <p class="text-xs font-bold text-slate-400">{{ isMeditationReport ? '最高稳定度' : '最高反馈值' }}</p>
              <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(displayReport.max_score) }}</p>
            </div>
            <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
              <p class="text-xs font-bold text-slate-400">稳定达标时长</p>
              <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(displayReport.stable_duration_sec, 's') }}</p>
            </div>
            <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
              <p class="text-xs font-bold text-slate-400">训练时长</p>
              <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(displayReport.duration_sec, 's') }}</p>
            </div>
          </div>

          <div v-if="isMeditationReport" class="rounded-3xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <p class="text-sm font-black text-slate-900 dark:text-white">脑机交互冥想指标</p>
            <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
                <p class="text-xs font-bold text-slate-400">视频</p>
                <p class="mt-2 text-sm font-black text-slate-900 dark:text-white">{{ meditationVideo.name || '--' }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ meditationVideo.id || '--' }} · {{ meditationVideo.type || '--' }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
                <p class="text-xs font-bold text-slate-400">Alpha / Theta / Beta</p>
                <p class="mt-2 text-sm font-black text-slate-900 dark:text-white">{{ formatNumber(meditationMetrics.alphaRelaxation) }} / {{ formatNumber(meditationMetrics.thetaImmersion) }} / {{ formatNumber(meditationMetrics.betaTension) }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
                <p class="text-xs font-bold text-slate-400">注意 / 呼吸放松</p>
                <p class="mt-2 text-sm font-black text-slate-900 dark:text-white">{{ formatNumber(meditationMetrics.attentionStability) }} / {{ formatNumber(meditationMetrics.breathingRelaxation) }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
                <p class="text-xs font-bold text-slate-400">HR / HRV / GSR / 质量</p>
                <p class="mt-2 text-sm font-black text-slate-900 dark:text-white">{{ formatNumber(meditationMetrics.heartRate, ' bpm') }} / {{ formatNumber(meditationMetrics.hrv, ' ms') }} / {{ formatNumber(meditationMetrics.gsr, ' mV') }} / {{ formatNumber(meditationMetrics.signalQuality, '%') }}</p>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-black text-slate-900 dark:text-white">反馈趋势</p>
                <p class="mt-1 text-xs font-bold text-slate-400">保存少量趋势点，不包含原始 EEG 数据</p>
              </div>
              <TrendingUp class="h-5 w-5 text-cyan-600" />
            </div>
            <svg class="mt-4 h-36 w-full" viewBox="0 0 320 96" preserveAspectRatio="none" role="img" aria-label="训练报告趋势图">
              <line x1="0" y1="48" x2="320" y2="48" class="stroke-slate-100 dark:stroke-slate-800" stroke-width="1" />
              <polyline v-if="trendPoints" :points="trendPoints" fill="none" stroke="#0891b2" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" />
            </svg>
          </div>

          <div class="grid gap-4 lg:grid-cols-2">
            <div class="rounded-3xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center gap-2 text-sm font-black text-slate-900 dark:text-white">
                <Activity class="h-5 w-5 text-cyan-600" />
                基本信息
              </div>
              <div class="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                <p>报告 ID：{{ displayReport.id }}</p>
                <p>任务类型：{{ taskTypeLabel(displayReport.task_type) }}</p>
                <p>训练指标：{{ metricLabel(displayReport.protocol_key) }}</p>
                <p>结束时间：{{ formatDate(displayReport.ended_at) }}</p>
              </div>
            </div>

            <div class="rounded-3xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <p class="text-sm font-black text-slate-900 dark:text-white">训练建议</p>
              <p class="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300">{{ displayReport.suggestion || '建议保持稳定练习，后续结合多次报告观察趋势。' }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>
