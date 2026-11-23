<script setup lang="ts">
import { trendLabel } from '@/lib/chart-labels'
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, BrainCircuit, Pause, Play, RotateCcw, Sparkles, TimerReset, Waves } from 'lucide-vue-next'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import { createBrainInterventionReport } from '@/db/api'
import { MockNeurofeedbackFeatureSource, type NeurofeedbackMetric } from '@/neurofeedback/featureSources'

type TrainingStageKey = 'connect' | 'baseline' | 'feedback'

interface TrainingStage {
  key: TrainingStageKey
  title: string
  durationSec: number
}

interface MetricConfig {
  key: NeurofeedbackMetric
  label: string
  targetLabel: string
  guidance: string
  low: number
  good: number
  color: string
  icon: unknown
}

const stageOrder = [
  { key: 'connect', title: '连接与信号检查', durationSec: 10 },
  { key: 'baseline', title: '基线采集', durationSec: 15 },
  { key: 'feedback', title: '反馈训练', durationSec: 60 },
] satisfies [TrainingStage, ...TrainingStage[]]

const metrics = [
  {
    key: 'alpha',
    label: 'Alpha 8–12Hz',
    targetLabel: '放松与稳定注意',
    guidance: '请保持身体稳定，减少眨眼、咬牙和肩颈动作。可以轻轻闭眼或半闭眼，将注意力放在呼吸上。不要刻意用力控制大脑，只需要让身体逐渐放松。当 Alpha 指标升高时，反馈动画会变得更稳定。',
    low: 45,
    good: 65,
    color: '#0284c7',
    icon: Waves,
  },
  {
    key: 'theta',
    label: 'Theta 4–8Hz',
    targetLabel: '深度放松 / 内在觉察',
    guidance: '请保持安静坐姿，放慢呼吸，将注意力转向身体内部感受。避免昏睡，保持清醒的放松。',
    low: 40,
    good: 58,
    color: '#7c3aed',
    icon: Sparkles,
  },
  {
    key: 'beta',
    label: 'Beta 13–30Hz',
    targetLabel: '清醒度 / 任务投入',
    guidance: '请睁眼，保持清醒和稳定注意。可以将注意力放在屏幕中央，减少走神和身体动作。',
    low: 48,
    good: 66,
    color: '#db2777',
    icon: Activity,
  },
  {
    key: 'smr',
    label: 'SMR 12–15Hz',
    targetLabel: '身体稳定',
    guidance: '请保持身体不动，放松肩颈和面部肌肉。目标不是紧张用力，而是在清醒状态下保持身体稳定。',
    low: 46,
    good: 64,
    color: '#059669',
    icon: BrainCircuit,
  },
  {
    key: 'thetaBetaRatio',
    label: 'Theta/Beta Ratio',
    targetLabel: '注意状态平稳',
    guidance: '请保持稳定注意，减少走神、眨眼和身体动作。目标是让注意状态更加平稳。',
    low: 42,
    good: 60,
    color: '#d97706',
    icon: TimerReset,
  },
] satisfies [MetricConfig, ...MetricConfig[]]

const totalDurationMs = stageOrder.reduce((sum, stage) => sum + stage.durationSec * 1000, 0)
const timerStepMs = 250
const router = useRouter()

const selectedMetric = ref<NeurofeedbackMetric>('alpha')
const currentStageIndex = ref(0)
const stageRemainingMs = ref(stageOrder[0].durationSec * 1000)
const feedbackValue = ref(0)
const trend = ref<number[]>([])
const running = ref(false)
const completed = ref(false)
const savingReport = ref(false)
const saveError = ref('')
const savedReportId = ref('')
const lastSampleAtMs = ref<number | null>(null)
const sessionStartedAtMs = ref<number>(Date.now())

const source = new MockNeurofeedbackFeatureSource(400)
let tickTimer: number | null = null

const currentStage = computed(() => stageAt(currentStageIndex.value))
const metricConfig = computed(() => metricByKey(selectedMetric.value))
const stageIndexLabel = computed(() => `${Math.min(currentStageIndex.value + 1, stageOrder.length)} / ${stageOrder.length}`)
const stageProgress = computed(() => {
  const duration = currentStage.value.durationSec * 1000
  if (duration <= 0) return 0
  return Math.round(((duration - stageRemainingMs.value) / duration) * 100)
})
const overallProgress = computed(() => {
  if (completed.value) return 100
  const completedStagesMs = stageOrder
    .slice(0, currentStageIndex.value)
    .reduce((sum, stage) => sum + stage.durationSec * 1000, 0)
  return Math.round(((completedStagesMs + (currentStage.value.durationSec * 1000 - stageRemainingMs.value)) / totalDurationMs) * 100)
})
const stateLabel = computed(() => {
  const { low, good } = metricConfig.value
  if (feedbackValue.value < low) return '低'
  if (feedbackValue.value < good) return '稳定中'
  return '良好'
})
const statusTone = computed(() => {
  if (stateLabel.value === '良好') return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200'
  if (stateLabel.value === '稳定中') return 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-200'
  return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
})
const ringStyle = computed(() => ({
  background: `conic-gradient(${metricConfig.value.color} ${feedbackValue.value}%, rgba(148, 163, 184, 0.16) 0)`,
}))
const pulseStyle = computed(() => ({
  transform: `scale(${0.94 + feedbackValue.value / 500})`,
  backgroundColor: `${metricConfig.value.color}12`,
}))
const trendPoints = computed(() => polylinePoints(trend.value))
const stageText = computed(() => currentStage.value.title)
const currentMetricText = computed(() => metricConfig.value.label)

function startTimer() {
  if (tickTimer !== null) return
  tickTimer = window.setInterval(() => {
    if (!running.value || completed.value) return
    stageRemainingMs.value = Math.max(0, stageRemainingMs.value - timerStepMs)
    if (stageRemainingMs.value === 0) advanceStage()
  }, timerStepMs)
}

function stopTimer() {
  if (tickTimer === null) return
  window.clearInterval(tickTimer)
  tickTimer = null
}

function handleSample(sample: { value: number; timestampMs: number }) {
  lastSampleAtMs.value = sample.timestampMs
  feedbackValue.value = clamp(feedbackValue.value + (sample.value - feedbackValue.value) * 0.22, 0, 100)
  trend.value = [...trend.value.slice(-119), Math.round(feedbackValue.value * 10) / 10]
}

function startSession() {
  if (completed.value) resetSession()
  if (running.value) return
  running.value = true
  sessionStartedAtMs.value = Date.now()
  startTimer()
  source.start(selectedMetric.value, handleSample)
}

function pauseSession() {
  if (!running.value) return
  running.value = false
  stopTimer()
  source.stop()
}

function resetSession() {
  pauseSession()
  currentStageIndex.value = 0
  stageRemainingMs.value = stageAt(0).durationSec * 1000
  feedbackValue.value = 0
  trend.value = []
  completed.value = false
  savingReport.value = false
  saveError.value = ''
  savedReportId.value = ''
  lastSampleAtMs.value = null
  sessionStartedAtMs.value = Date.now()
}

function selectMetric(metric: NeurofeedbackMetric) {
  if (metric === selectedMetric.value) return
  const shouldResume = running.value
  resetSession()
  selectedMetric.value = metric
  if (shouldResume) startSession()
}

function advanceStage() {
  const nextIndex = currentStageIndex.value + 1
  if (nextIndex >= stageOrder.length) {
    completed.value = true
    running.value = false
    stopTimer()
    source.stop()
    stageRemainingMs.value = 0
    void saveReport()
    return
  }

  currentStageIndex.value = nextIndex
  stageRemainingMs.value = stageAt(nextIndex).durationSec * 1000
}

function stageAt(index: number): TrainingStage {
  return stageOrder[index] ?? stageOrder[0]
}

function metricByKey(metric: NeurofeedbackMetric): MetricConfig {
  return metrics.find((item) => item.key === metric) || metrics[0]
}

function protocolKeyForMetric(metric: NeurofeedbackMetric) {
  return {
    alpha: 'alpha_uptraining',
    theta: 'theta_training',
    beta: 'beta_training',
    smr: 'smr_training',
    thetaBetaRatio: 'theta_beta_ratio',
  }[metric]
}

function taskNameForMetric(metric: NeurofeedbackMetric) {
  return `${metricByKey(metric).label} Training`
}

async function saveReport() {
  if (savingReport.value || savedReportId.value) return
  savingReport.value = true
  saveError.value = ''
  try {
    const report = await createBrainInterventionReport({
      task_type: 'neurofeedback',
      task_name: taskNameForMetric(selectedMetric.value),
      protocol_key: protocolKeyForMetric(selectedMetric.value),
      started_at: new Date(sessionStartedAtMs.value).toISOString(),
      ended_at: new Date().toISOString(),
      duration_sec: Math.max(1, Math.round((Date.now() - sessionStartedAtMs.value) / 1000)),
      status: 'completed',
      main_score: feedbackValue.value,
      avg_score: avgTrendValue(),
      max_score: trend.value.length ? Math.max(...trend.value) : feedbackValue.value,
      stable_duration_sec: stableSeconds(),
      signal_quality_avg: 0.92,
      artifact_ratio: 0.08,
      summary: `${metricConfig.value.label} 训练已完成，当前记录用于回顾训练过程。`,
      suggestion: suggestionText(),
      metrics_json: {
        metric: selectedMetric.value,
        latestFeedback: feedbackValue.value,
        avgFeedback: avgTrendValue(),
        maxFeedback: trend.value.length ? Math.max(...trend.value) : feedbackValue.value,
        stableDurationSec: stableSeconds(),
        signalQualityAvg: 0.92,
        artifactRatio: 0.08,
      },
      curve_json: {
        values: trend.value.slice(-120),
      },
      config_json: {
        stageOrder,
        selectedMetric: selectedMetric.value,
      },
    })
    savedReportId.value = report.id
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : '训练报告保存失败'
  } finally {
    savingReport.value = false
  }
}

function avgTrendValue() {
  if (trend.value.length === 0) return feedbackValue.value
  return trend.value.reduce((sum, value) => sum + value, 0) / trend.value.length
}

function stableSeconds() {
  const config = metricConfig.value
  const stableCount = trend.value.filter((value) => value >= config.good).length
  return stableCount * (timerStepMs / 1000)
}

function suggestionText() {
  if (feedbackValue.value >= metricConfig.value.good) {
    return '建议保持当前训练节奏，后续继续观察多次训练的趋势变化。'
  }
  if (feedbackValue.value >= metricConfig.value.low) {
    return '建议减少动作干扰，持续保持舒适、稳定的训练节奏。'
  }
  return '建议先确认佩戴状态和环境稳定性，再进行下一次训练。'
}

function formatSeconds(ms: number) {
  return Math.max(0, Math.ceil(ms / 1000))
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function polylinePoints(values: number[]) {
  if (values.length < 2) return ''

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 320
  const height = 88
  const last = values.length - 1
  return values
    .map((value, index) => {
      const x = (index / last) * width
      const y = height - ((value - min) / range) * height
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

onBeforeUnmount(() => {
  stopTimer()
  source.stop()
})
</script>

<template>
  <section class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-lg shadow-cyan-100/40 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="space-y-2">
        <div class="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-200">
          <BrainCircuit class="h-4 w-4" />
          Web EEG Neurofeedback Training Demo
        </div>
        <h2 class="text-xl font-black text-slate-900 dark:text-white">实时神经反馈训练</h2>
        <p class="max-w-3xl text-sm leading-7 text-slate-500 dark:text-slate-300">
          当前版本先完成 Alpha Uptraining 的完整流程，并保留后续切换到真实 EEG WebSocket 的入口。
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-700 transition hover:border-cyan-300 hover:text-cyan-700 dark:border-slate-700 dark:text-slate-200" type="button" @click="running ? pauseSession() : startSession()">
          <Pause v-if="running" class="h-4 w-4" />
          <Play v-else class="h-4 w-4" />
          {{ running ? '暂停' : completed ? '重新开始' : '开始训练' }}
        </button>
        <button class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100" type="button" @click="resetSession">
          <RotateCcw class="h-4 w-4" />
          重置
        </button>
      </div>
    </div>

    <div class="mt-5 flex flex-wrap gap-2">
      <button
        v-for="metric in metrics"
        :key="metric.key"
        type="button"
        class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
        :class="selectedMetric === metric.key ? 'border-transparent text-white shadow-sm' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300'"
        :style="selectedMetric === metric.key ? { backgroundColor: metric.color } : undefined"
        @click="selectMetric(metric.key)"
      >
        <component :is="metric.icon" class="h-4 w-4" />
        {{ metric.label }}
      </button>
    </div>

    <div v-if="saveError" class="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ saveError }}</div>
    <div v-else-if="savedReportId" class="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm font-bold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">
      训练报告已保存。
      <button class="ml-2 underline" type="button" @click="router.push(`/brain-intervention/reports/${savedReportId}`)">查看报告</button>
    </div>

    <div class="mt-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
            <p class="text-xs font-bold text-slate-400">当前训练目标</p>
            <p class="mt-2 text-lg font-black text-slate-900 dark:text-white">{{ currentMetricText }}</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ metricConfig.targetLabel }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
            <p class="text-xs font-bold text-slate-400">当前训练阶段</p>
            <p class="mt-2 text-lg font-black text-slate-900 dark:text-white">{{ completed ? '训练完成' : stageText }}</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ stageIndexLabel }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
            <p class="text-xs font-bold text-slate-400">实时反馈值</p>
            <p class="mt-2 text-3xl font-black text-slate-900 dark:text-white">{{ feedbackValue.toFixed(1) }}</p>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">0 - 100</p>
          </div>
          <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-950">
            <p class="text-xs font-bold text-slate-400">当前状态</p>
            <span :class="['mt-2 inline-flex rounded-full px-3 py-1 text-sm font-bold', statusTone]">{{ stateLabel }}</span>
            <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ running ? '训练进行中' : completed ? '可重新开始' : '等待开始' }}</p>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-[220px_1fr]">
          <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <div class="mx-auto flex h-48 w-48 items-center justify-center rounded-full p-3" :style="ringStyle">
              <div class="grid h-full w-full place-items-center rounded-full bg-white shadow-sm dark:bg-slate-900" :style="pulseStyle">
                <div class="text-center">
                  <p class="text-xs font-bold text-slate-400">反馈圆环</p>
                  <p class="mt-1 text-4xl font-black text-slate-900 dark:text-white">{{ feedbackValue.toFixed(0) }}</p>
                  <p class="mt-1 text-sm font-bold" :style="{ color: metricConfig.color }">{{ stateLabel }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-black text-slate-900 dark:text-white">趋势线</p>
                <p class="mt-1 text-xs font-bold text-slate-400">最近 {{ trend.length }} 个点，最多保留 120 个点</p>
              </div>
              <p class="text-xs font-bold text-slate-400">{{ lastSampleAtMs ? '已接收特征流' : '等待特征流' }}</p>
            </div>
            <svg class="mt-4 h-24 w-full" viewBox="0 0 320 88" preserveAspectRatio="none" role="img" :aria-label="trendLabel(`${metricConfig.label}反馈值`, trend)">
              <line x1="0" y1="44" x2="320" y2="44" class="stroke-slate-100 dark:stroke-slate-800" stroke-width="1" />
              <polyline v-if="trendPoints" :points="trendPoints" fill="none" :stroke="metricConfig.color" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" />
            </svg>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-black text-slate-900 dark:text-white">训练进度</p>
              <p class="mt-1 text-xs font-bold text-slate-400">
                {{ overallProgress }}% · {{ completed ? '已完成' : `${formatSeconds(stageRemainingMs)}s` }}
              </p>
            </div>
            <p class="text-xs font-bold text-slate-400">{{ stageProgress }}% 当前阶段</p>
          </div>
          <div class="mt-3">
            <ProgressBar :value="overallProgress" label="脑电反馈训练进度" :tone="completed ? 'from-emerald-500 to-cyan-500' : 'from-cyan-500 to-blue-500'" />
          </div>
        </div>
      </div>

      <aside class="space-y-4">
        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
          <p class="text-sm font-black text-slate-900 dark:text-white">引导语</p>
          <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">{{ metricConfig.guidance }}</p>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <p class="text-sm font-black text-slate-900 dark:text-white">训练流程</p>
          <div class="mt-4 space-y-3">
            <div
              v-for="(stage, index) in stageOrder"
              :key="stage.key"
              class="rounded-2xl px-3 py-3"
              :class="index < currentStageIndex ? 'bg-emerald-50 dark:bg-emerald-950/20' : index === currentStageIndex ? 'bg-cyan-50 dark:bg-cyan-950/20' : 'bg-slate-50 dark:bg-slate-900'"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-bold text-slate-900 dark:text-white">{{ stage.title }}</p>
                <p class="text-xs font-bold text-slate-400">{{ stage.durationSec }}s</p>
              </div>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                <span v-if="index < currentStageIndex">已完成</span>
                <span v-else-if="index === currentStageIndex">{{ completed ? '完成' : `${formatSeconds(stageRemainingMs)}s` }}</span>
                <span v-else>待开始</span>
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>
