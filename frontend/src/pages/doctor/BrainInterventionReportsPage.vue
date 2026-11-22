<script setup lang="ts">
import { BrainCircuit, Filter, Loader2, Search, TrendingUp } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { getAllProfiles, getBrainInterventionReport, getBrainInterventionReports } from '@/db/api'
import type { BrainInterventionReport, Profile } from '@/types'

const reports = ref<BrainInterventionReport[]>([])
const selectedReport = ref<BrainInterventionReport | null>(null)
const patients = ref<Profile[]>([])
const loading = ref(false)
const errorMessage = ref('')
const filters = ref({
  user_id: '',
  task_type: '',
  protocol_key: '',
  started_from: '',
  started_to: '',
})

const trendValues = computed(() => {
  const curve = selectedReport.value?.curve_json || {}
  const values = Array.isArray(curve.values) ? curve.values : []
  return values.map((item) => Number(item)).filter((item) => Number.isFinite(item))
})
const trendPoints = computed(() => polylinePoints(trendValues.value))
const isMeditationReport = computed(() => selectedReport.value?.task_type === 'meditation_biosignal_monitor')
const meditationMetrics = computed(() => {
  const metrics = selectedReport.value?.metrics_json || {}
  return (metrics.averages || {}) as Record<string, number>
})
const meditationVideo = computed(() => {
  const metrics = selectedReport.value?.metrics_json || {}
  const config = selectedReport.value?.config_json || {}
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
    reports.value = await getBrainInterventionReports({
      user_id: filters.value.user_id || undefined,
      task_type: filters.value.task_type || undefined,
      protocol_key: filters.value.protocol_key || undefined,
      started_from: filters.value.started_from ? new Date(filters.value.started_from).toISOString() : undefined,
      started_to: filters.value.started_to ? new Date(filters.value.started_to).toISOString() : undefined,
    })
    if (!selectedReport.value || !reports.value.some((item) => item.id === selectedReport.value?.id)) {
      selectedReport.value = reports.value[0] || null
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '训练报告加载失败'
  } finally {
    loading.value = false
  }
}

const openReport = async (report: BrainInterventionReport) => {
  selectedReport.value = report
  selectedReport.value = await getBrainInterventionReport(report.id).catch(() => report)
}

const loadPatients = async () => {
  patients.value = (await getAllProfiles()).filter((item) => item.role === 'user')
}

onMounted(() => {
  void Promise.all([loadReports(), loadPatients()])
})

const patientName = (report: BrainInterventionReport) =>
  report.patient_full_name || report.patient_username || report.user_name || report.user_id

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
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-black text-slate-900 dark:text-white">用户训练报告</h1>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-300">查看不同脑机调控任务的训练记录。报告仅用于训练过程回顾，不作为疾病诊断或疗效判断。</p>
      </div>
      <div class="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-bold text-cyan-700 shadow-sm dark:bg-slate-900 dark:text-cyan-200">
        <BrainCircuit class="h-5 w-5" />
        {{ reports.length }} 份报告
      </div>
    </div>

    <section class="rounded-2xl border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div class="flex items-center gap-2 text-sm font-black text-slate-900 dark:text-white">
        <Filter class="h-5 w-5 text-cyan-600" />
        筛选
      </div>
      <div class="mt-4 grid gap-3 md:grid-cols-5">
        <select v-model="filters.user_id" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950">
          <option value="">全部用户</option>
          <option v-for="patient in patients" :key="patient.id" :value="patient.id">{{ patient.full_name || patient.username }}</option>
        </select>
        <select v-model="filters.task_type" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950">
          <option value="">全部任务类型</option>
          <option value="neurofeedback">Neurofeedback</option>
          <option value="meditation_biosignal_monitor">脑机交互冥想</option>
          <option value="ssvep">SSVEP</option>
          <option value="p300">P300</option>
          <option value="smr">SMR</option>
          <option value="relaxation">Relaxation</option>
          <option value="attention_training">Attention Training</option>
        </select>
        <select v-model="filters.protocol_key" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950">
          <option value="">全部训练指标</option>
          <option value="alpha_uptraining">Alpha</option>
          <option value="theta_training">Theta</option>
          <option value="beta_training">Beta</option>
          <option value="smr_training">SMR</option>
          <option value="theta_beta_ratio">Theta/Beta Ratio</option>
          <option value="meditation_biosignal_monitor">脑机交互冥想</option>
        </select>
        <input v-model="filters.started_from" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950" type="date" />
        <input v-model="filters.started_to" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950" type="date" />
        <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="loadReports">
          <Search class="h-4 w-4" />
          查询
        </button>
      </div>
    </section>

    <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>

    <div class="grid gap-5 xl:grid-cols-[420px_1fr]">
      <section class="rounded-2xl border border-slate-100 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div class="border-b border-slate-100 p-4 text-sm font-black text-slate-900 dark:border-slate-800 dark:text-white">报告列表</div>
        <div v-if="loading" class="flex items-center justify-center p-10 text-slate-500">
          <Loader2 class="mr-2 h-5 w-5 animate-spin" />
          加载中...
        </div>
        <div v-else class="divide-y divide-slate-100 dark:divide-slate-800">
          <button
            v-for="report in reports"
            :key="report.id"
            class="w-full p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
            :class="selectedReport?.id === report.id ? 'bg-cyan-50 dark:bg-cyan-950/20' : ''"
            type="button"
            @click="openReport(report)"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-black text-slate-900 dark:text-white">{{ patientName(report) }}</p>
                <p class="mt-1 text-sm font-bold text-slate-500">{{ report.task_name }} · {{ metricLabel(report.protocol_key) }}</p>
              </div>
              <span class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-500 dark:bg-slate-800">{{ taskTypeLabel(report.task_type) }}</span>
            </div>
            <p class="mt-2 text-xs text-slate-400">{{ formatDate(report.started_at) }}</p>
            <p class="mt-2 line-clamp-2 text-sm text-slate-500 dark:text-slate-300">{{ report.summary || '训练报告已生成。' }}</p>
          </button>
          <div v-if="reports.length === 0" class="p-10 text-center text-sm text-slate-500">暂无训练报告</div>
        </div>
      </section>

      <section v-if="selectedReport" class="space-y-5">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p class="text-sm font-bold text-cyan-700 dark:text-cyan-200">{{ patientName(selectedReport) }}</p>
          <h2 class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ selectedReport.task_name }}</h2>
          <p class="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-300">{{ selectedReport.summary || '训练报告已生成。' }}</p>
        </div>

        <div class="grid gap-3 md:grid-cols-4">
          <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
            <p class="text-xs font-bold text-slate-400">{{ isMeditationReport ? '平均冥想稳定度' : '平均反馈值' }}</p>
            <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(selectedReport.avg_score) }}</p>
          </div>
          <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
            <p class="text-xs font-bold text-slate-400">{{ isMeditationReport ? '最高稳定度' : '最高反馈值' }}</p>
            <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(selectedReport.max_score) }}</p>
          </div>
          <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
            <p class="text-xs font-bold text-slate-400">稳定达标时长</p>
            <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(selectedReport.stable_duration_sec, 's') }}</p>
          </div>
          <div class="rounded-2xl bg-white p-4 dark:bg-slate-900">
            <p class="text-xs font-bold text-slate-400">训练时长</p>
            <p class="mt-2 text-2xl font-black text-slate-900 dark:text-white">{{ formatNumber(selectedReport.duration_sec, 's') }}</p>
          </div>
        </div>

        <div v-if="isMeditationReport" class="rounded-2xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p class="text-sm font-black text-slate-900 dark:text-white">脑机交互冥想指标</p>
          <div class="mt-4 grid gap-3 md:grid-cols-4">
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

        <div class="rounded-2xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-black text-slate-900 dark:text-white">趋势图</p>
              <p class="mt-1 text-xs font-bold text-slate-400">轻量趋势点，不包含原始 EEG</p>
            </div>
            <TrendingUp class="h-5 w-5 text-cyan-600" />
          </div>
          <svg class="mt-4 h-40 w-full" viewBox="0 0 320 96" preserveAspectRatio="none" role="img" aria-label="医生端训练报告趋势图">
            <line x1="0" y1="48" x2="320" y2="48" class="stroke-slate-100 dark:stroke-slate-800" stroke-width="1" />
            <polyline v-if="trendPoints" :points="trendPoints" fill="none" stroke="#0891b2" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" />
          </svg>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <div class="rounded-2xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <p class="text-sm font-black text-slate-900 dark:text-white">基本信息</p>
            <div class="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
              <p>报告 ID：{{ selectedReport.id }}</p>
              <p>用户 ID：{{ selectedReport.user_id }}</p>
              <p>任务类型：{{ taskTypeLabel(selectedReport.task_type) }}</p>
              <p>训练指标：{{ metricLabel(selectedReport.protocol_key) }}</p>
              <p>训练时间：{{ formatDate(selectedReport.started_at) }}</p>
            </div>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <p class="text-sm font-black text-slate-900 dark:text-white">训练建议</p>
            <p class="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300">{{ selectedReport.suggestion || '建议结合多次训练记录观察趋势变化。' }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
