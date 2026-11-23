<script setup lang="ts">
import { trendLabel } from '@/lib/chart-labels'
import { Activity, Brain, CheckCircle2, Droplets, HeartPulse, Loader2, Pause, Play, Sparkles, Square, TrendingUp, Video } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createBrainInterventionReport, getHealingContents } from '@/db/api'
import { GatewaySensorSource } from '@/sensors/GatewaySensorSource'
import { SensorStreamManager } from '@/sensors/SensorStreamManager'
import type { SignalSnapshot } from '@/sensors/types'
import type { HealingContent } from '@/types'
import { publicAssetUrl } from '@/utils/public-assets'

interface MeditationVideo {
  id: string
  title: string
  type: string
  url: string
  durationSec: number
  description: string
  tags: string[]
}

interface MeditationMetrics {
  stability: number
  alphaRelaxation: number
  thetaImmersion: number
  betaTension: number
  attentionStability: number
  breathingRelaxation: number
  heartRate: number
  hrv: number
  gsr: number
  signalQuality: number
}

interface TrendPoint extends MeditationMetrics {
  t: number
}

interface MetricCard {
  key: keyof MeditationMetrics
  title: string
  unit: string
  range: string
  hint: string
  icon: unknown
  color: string
}

const router = useRouter()
const videoRef = ref<HTMLVideoElement | null>(null)
const videos = ref<MeditationVideo[]>([])
const selectedVideoId = ref('')
const loadingVideos = ref(false)
const videoError = ref('')
const running = ref(false)
const paused = ref(false)
const completed = ref(false)
const connecting = ref(false)
const gatewayError = ref('')
const savingReport = ref(false)
const saveError = ref('')
const savedReportId = ref('')
const startedAtMs = ref<number | null>(null)
const activeMs = ref(0)
const frameTick = ref(0)
const metrics = ref<MeditationMetrics>({
  stability: 52,
  alphaRelaxation: 50,
  thetaImmersion: 48,
  betaTension: 42,
  attentionStability: 55,
  breathingRelaxation: 54,
  heartRate: 75,
  hrv: 42,
  gsr: 16,
  signalQuality: 70,
})
const trend = ref<TrendPoint[]>([])
const hrWindow = ref<number[]>([])

const source = new GatewaySensorSource()
const manager = new SensorStreamManager(8)
const updateMs = 500
let unsubscribe: (() => void) | null = null
let unsubscribeStatus: (() => void) | null = null
let metricTimer = 0
let runStartedAtMs = 0
let lastBatchAtMs = 0

const metricCards: MetricCard[] = [
  { key: 'stability', title: '冥想稳定度', unit: '', range: '0-100，越高越稳定', hint: '综合 EEG、心率、HRV、皮肤电和信号质量。', icon: Sparkles, color: '#0891b2' },
  { key: 'alphaRelaxation', title: 'Alpha 放松指数', unit: '', range: '0-100，60 以上较好', hint: '放松状态参考。', icon: Brain, color: '#2563eb' },
  { key: 'thetaImmersion', title: 'Theta 沉浸指数', unit: '', range: '0-100，55 以上较好', hint: '内在专注和沉浸参考。', icon: Brain, color: '#7c3aed' },
  { key: 'betaTension', title: 'Beta 紧张指数', unit: '', range: '0-100，越低越放松', hint: '紧张、用力或高唤醒参考。', icon: Activity, color: '#db2777' },
  { key: 'attentionStability', title: '注意稳定度', unit: '', range: '0-100，60 以上较好', hint: '关注练习内容的稳定程度参考。', icon: TrendingUp, color: '#059669' },
  { key: 'breathingRelaxation', title: '呼吸放松度', unit: '', range: '0-100，60 以上较好', hint: '由心率平稳度和皮肤电变化估算。', icon: HeartPulse, color: '#0d9488' },
  { key: 'heartRate', title: '心率 HR', unit: 'bpm', range: '参考 60-100 bpm', hint: '生理唤醒水平参考。', icon: HeartPulse, color: '#e11d48' },
  { key: 'hrv', title: '心率变异性 HRV', unit: 'ms', range: '参考 30-80 ms', hint: '放松与自主神经稳定性参考。', icon: Activity, color: '#f59e0b' },
  { key: 'gsr', title: '皮肤电 EDA/GSR', unit: 'mV', range: '相对变化参考', hint: '压力或唤醒变化参考。', icon: Droplets, color: '#14b8a6' },
  { key: 'signalQuality', title: '综合信号质量', unit: '%', range: '80% 以上较好', hint: '设备接触和动作干扰参考。', icon: CheckCircle2, color: '#16a34a' },
]

const selectedVideo = computed(() => videos.value.find((item) => item.id === selectedVideoId.value) || videos.value[0] || null)
const elapsedSeconds = computed(() => {
  frameTick.value
  return Math.max(0, Math.round(currentActiveMs() / 1000))
})
const statusText = computed(() => {
  if (savingReport.value) return '报告保存中'
  if (completed.value) return '练习已结束'
  if (running.value) return '练习进行中'
  if (paused.value) return '已暂停'
  return '等待开始'
})
const advice = computed(() => buildAdvice(metrics.value))
const trendPoints = computed(() => polylinePoints(trend.value.map((item) => item.stability)))
const detailMetricCards = computed(() => metricCards.filter((card) => card.key !== 'stability'))
const connected = computed(() => {
  frameTick.value
  return !gatewayError.value && lastBatchAtMs > 0 && Date.now() - lastBatchAtMs < 3000
})

onMounted(() => {
  void loadVideos()
})

onBeforeUnmount(() => {
  stopMetricTimer()
  disconnectGateway()
})

async function loadVideos() {
  loadingVideos.value = true
  videoError.value = ''
  try {
    const contents = await getHealingContents()
    const videoContents = contents
      .filter((item) => item.content_type === 'video')
      .map(toMeditationVideo)
      .filter((item): item is MeditationVideo => Boolean(item))
    const meditationVideos = videoContents.filter((item) => isMeditationVideo(item))
    videos.value = [...meditationVideos, ...videoContents.filter((item) => !meditationVideos.some((video) => video.id === item.id))]
    if (!videos.value.some((item) => item.url.includes('正念冥想.mp4'))) {
      videos.value.push({
        id: 'local-mindfulness-video',
        title: '正念冥想',
        type: 'video',
        url: publicAssetUrl('/srcs/video/正念冥想.mp4'),
        durationSec: 600,
        description: '本地正念冥想视频，可作为系统视频资源不足时的练习内容。',
        tags: ['正念', '冥想', '视频'],
      })
    }
    selectedVideoId.value = videos.value[0]?.id || ''
  } catch (error) {
    videoError.value = error instanceof Error ? error.message : '冥想视频加载失败'
    videos.value = [{
      id: 'local-mindfulness-video',
      title: '正念冥想',
      type: 'video',
      url: publicAssetUrl('/srcs/video/正念冥想.mp4'),
      durationSec: 600,
      description: '本地正念冥想视频。',
      tags: ['正念', '冥想', '视频'],
    }]
    selectedVideoId.value = videos.value[0]?.id || ''
  } finally {
    loadingVideos.value = false
  }
}

function toMeditationVideo(content: HealingContent): MeditationVideo | null {
  const url = publicAssetUrl(content.content_url)
  if (!url) return null
  return {
    id: content.id,
    title: content.title,
    type: content.content_type,
    url,
    durationSec: Number(content.duration || 0) || 600,
    description: content.description || '',
    tags: Array.isArray(content.tags) ? content.tags : [],
  }
}

function isMeditationVideo(video: MeditationVideo) {
  const text = `${video.title} ${video.description} ${video.tags.join(' ')}`.toLowerCase()
  return ['冥想', '正念', '呼吸', '放松', '睡眠', 'meditation', 'mindfulness', 'relax'].some((key) => text.includes(key))
}

async function startSession() {
  if (!selectedVideo.value || running.value || savingReport.value) return
  if (completed.value) resetSession()
  if (!startedAtMs.value) startedAtMs.value = Date.now()
  running.value = true
  paused.value = false
  runStartedAtMs = Date.now()
  await connectGateway()
  startMetricTimer()
  await videoRef.value?.play().catch(() => {})
}

function pauseSession() {
  if (!running.value) return
  activeMs.value += Date.now() - runStartedAtMs
  running.value = false
  paused.value = true
  videoRef.value?.pause()
  stopMetricTimer()
  disconnectGateway()
}

async function endSession() {
  if (!startedAtMs.value) return
  if (running.value) {
    activeMs.value += Date.now() - runStartedAtMs
  }
  running.value = false
  paused.value = false
  completed.value = true
  videoRef.value?.pause()
  stopMetricTimer()
  disconnectGateway()
  await saveReport()
}

function resetSession() {
  running.value = false
  paused.value = false
  completed.value = false
  savingReport.value = false
  saveError.value = ''
  savedReportId.value = ''
  startedAtMs.value = null
  activeMs.value = 0
  runStartedAtMs = 0
  trend.value = []
  hrWindow.value = []
  metrics.value = {
    stability: 52,
    alphaRelaxation: 50,
    thetaImmersion: 48,
    betaTension: 42,
    attentionStability: 55,
    breathingRelaxation: 54,
    heartRate: 75,
    hrv: 42,
    gsr: 16,
    signalQuality: 70,
  }
  if (videoRef.value) videoRef.value.currentTime = 0
}

async function connectGateway() {
  if (connecting.value || source.getStatus() === 'connected') return
  connecting.value = true
  gatewayError.value = ''
  if (!unsubscribe) {
    unsubscribe = source.subscribe((batch) => {
      lastBatchAtMs = Date.now()
      manager.push(batch)
    })
  }
  if (!unsubscribeStatus) {
    unsubscribeStatus = source.subscribeStatus((status) => {
      if (status === 'error') gatewayError.value = '传感器网关连接异常'
      if (status === 'connected') gatewayError.value = ''
    })
  }
  try {
    await source.connect()
  } catch (error) {
    gatewayError.value = error instanceof Error ? error.message : '传感器网关连接失败'
  } finally {
    connecting.value = false
  }
}

function disconnectGateway() {
  source.disconnect()
  if (unsubscribe) unsubscribe()
  if (unsubscribeStatus) unsubscribeStatus()
  unsubscribe = null
  unsubscribeStatus = null
}

function startMetricTimer() {
  if (metricTimer) return
  updateMetrics()
  metricTimer = window.setInterval(updateMetrics, updateMs)
}

function stopMetricTimer() {
  if (!metricTimer) return
  window.clearInterval(metricTimer)
  metricTimer = 0
}

function updateMetrics() {
  const eeg = manager.snapshot('eeg', 64)
  const ppg = manager.snapshot('ppg', 64)
  const gsr = manager.snapshot('gsr', 64)
  const target = deriveMetrics(eeg, ppg, gsr)
  metrics.value = smoothMetrics(metrics.value, target, 0.18)
  const point: TrendPoint = { ...metrics.value, t: elapsedSeconds.value }
  trend.value = [...trend.value.slice(-239), point]
  frameTick.value += 1
}

function deriveMetrics(eeg: SignalSnapshot | null, ppg: SignalSnapshot | null, gsr: SignalSnapshot | null): MeditationMetrics {
  const t = Date.now() / 1000
  const eegValues = eeg?.channels
    .filter((channel) => channel.name.endsWith('_processed_uV'))
    .map((channel) => Math.abs(channel.latestValue ?? 0))
    .filter((value) => Number.isFinite(value)) || []
  const eegMotion = eegValues.length ? average(eegValues) : 8
  const motionPenalty = clamp(eegMotion / 28, 0, 1)
  const hr = latestChannel(ppg, 'HR_bpm') ?? (74 + Math.sin(t / 7) * 4)
  const gsrMv = latestChannel(gsr, 'GSR_display_mV') ?? latestChannel(gsr, 'GSR_physical_mV') ?? (16 + Math.sin(t / 9) * 2)
  hrWindow.value = [...hrWindow.value.slice(-35), hr]
  const hrSpread = hrWindow.value.length > 4 ? standardDeviation(hrWindow.value) : 4
  const hrv = clamp(62 - hrSpread * 4 - Math.max(0, hr - 78) * 0.55 + Math.sin(t / 8) * 4, 18, 82)
  const hrStress = clamp((hr - 72) / 26, 0, 1)
  const gsrStress = clamp((gsrMv - 16) / 18, 0, 1)
  const hasSignal = Boolean(eeg || ppg || gsr)
  const quality = clamp((hasSignal ? 88 : 46) - motionPenalty * 22 - (gatewayError.value ? 18 : 0), 15, 96)
  const alpha = clamp(66 + Math.sin(t / 6) * 8 - hrStress * 12 - motionPenalty * 15 + quality * 0.08, 20, 95)
  const theta = clamp(58 + Math.sin(t / 10 + 0.8) * 9 - motionPenalty * 10 - Math.max(0, hr - 86) * 0.25, 18, 92)
  const beta = clamp(35 + hrStress * 28 + gsrStress * 20 + motionPenalty * 18 + Math.sin(t / 5) * 5, 12, 90)
  const attention = clamp(60 + theta * 0.18 + alpha * 0.12 - beta * 0.22 - motionPenalty * 12, 20, 95)
  const breathing = clamp(66 + hrv * 0.25 - hrStress * 18 - gsrStress * 14 + Math.sin(t / 11) * 4, 18, 96)
  const stability = clamp(alpha * 0.25 + theta * 0.16 + attention * 0.18 + breathing * 0.18 + (100 - beta) * 0.13 + quality * 0.1, 0, 100)
  return {
    stability,
    alphaRelaxation: alpha,
    thetaImmersion: theta,
    betaTension: beta,
    attentionStability: attention,
    breathingRelaxation: breathing,
    heartRate: clamp(hr, 45, 125),
    hrv,
    gsr: clamp(gsrMv, 0, 80),
    signalQuality: quality,
  }
}

function latestChannel(snapshot: SignalSnapshot | null, name: string) {
  const value = snapshot?.channels.find((channel) => channel.name === name)?.latestValue
  return value === null || value === undefined || !Number.isFinite(value) ? null : value
}

function smoothMetrics(current: MeditationMetrics, target: MeditationMetrics, factor: number): MeditationMetrics {
  return Object.fromEntries(
    Object.entries(current).map(([key, value]) => {
      const targetValue = target[key as keyof MeditationMetrics]
      return [key, value + (targetValue - value) * factor]
    }),
  ) as MeditationMetrics
}

async function saveReport() {
  if (savingReport.value || savedReportId.value || !selectedVideo.value) return
  savingReport.value = true
  saveError.value = ''
  const averages = averageMetrics()
  const stateChange = stateChangeText()
  try {
    const report = await createBrainInterventionReport({
      task_type: 'meditation_biosignal_monitor',
      task_name: '脑机交互冥想',
      protocol_key: 'meditation_biosignal_monitor',
      started_at: new Date(startedAtMs.value || Date.now()).toISOString(),
      ended_at: new Date().toISOString(),
      duration_sec: Math.max(1, Math.round(activeMs.value / 1000)),
      status: 'completed',
      main_score: averages.stability,
      avg_score: averages.stability,
      max_score: maxMetric('stability'),
      stable_duration_sec: trend.value.filter((item) => item.stability >= 65).length * (updateMs / 1000),
      signal_quality_avg: averages.signalQuality / 100,
      artifact_ratio: clamp(1 - averages.signalQuality / 100, 0, 1),
      summary: `完成「${selectedVideo.value.title}」脑机交互冥想，平均稳定度 ${averages.stability.toFixed(1)}。${stateChange}`,
      suggestion: advice.value,
      metrics_json: {
        videoId: selectedVideo.value.id,
        videoName: selectedVideo.value.title,
        videoType: selectedVideo.value.type,
        durationSec: Math.max(1, Math.round(activeMs.value / 1000)),
        averages,
        mainStateChanges: stateChange,
        latest: metrics.value,
      },
      curve_json: {
        values: trend.value.slice(-120).map((item) => Number(item.stability.toFixed(1))),
        series: trend.value.slice(-120).map((item) => ({
          t: item.t,
          stability: round1(item.stability),
          alpha: round1(item.alphaRelaxation),
          theta: round1(item.thetaImmersion),
          beta: round1(item.betaTension),
          hr: round1(item.heartRate),
          hrv: round1(item.hrv),
          gsr: round1(item.gsr),
          quality: round1(item.signalQuality),
        })),
      },
      config_json: {
        taskType: 'meditation_biosignal_monitor',
        updateMs,
        video: selectedVideo.value,
        guidance: guidanceText,
      },
    })
    savedReportId.value = report.id
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : '冥想训练报告保存失败'
  } finally {
    savingReport.value = false
  }
}

function averageMetrics(): MeditationMetrics {
  const values = trend.value.length ? trend.value : [{ ...metrics.value, t: 0 }]
  return {
    stability: average(values.map((item) => item.stability)),
    alphaRelaxation: average(values.map((item) => item.alphaRelaxation)),
    thetaImmersion: average(values.map((item) => item.thetaImmersion)),
    betaTension: average(values.map((item) => item.betaTension)),
    attentionStability: average(values.map((item) => item.attentionStability)),
    breathingRelaxation: average(values.map((item) => item.breathingRelaxation)),
    heartRate: average(values.map((item) => item.heartRate)),
    hrv: average(values.map((item) => item.hrv)),
    gsr: average(values.map((item) => item.gsr)),
    signalQuality: average(values.map((item) => item.signalQuality)),
  }
}

function maxMetric(key: keyof MeditationMetrics) {
  return trend.value.length ? Math.max(...trend.value.map((item) => item[key])) : metrics.value[key]
}

function stateChangeText() {
  if (trend.value.length < 2) return '趋势数据较少。'
  const first = trend.value[0] || { ...metrics.value, t: 0 }
  const last = trend.value[trend.value.length - 1] || first
  const stabilityDelta = last.stability - first.stability
  const hrDelta = last.heartRate - first.heartRate
  const gsrDelta = last.gsr - first.gsr
  const stabilityText = stabilityDelta >= 3 ? '稳定度较开始提升' : stabilityDelta <= -3 ? '稳定度较开始下降' : '稳定度整体平稳'
  const hrText = hrDelta <= -3 ? '心率有所回落' : hrDelta >= 3 ? '心率有所升高' : '心率变化不大'
  const gsrText = gsrDelta <= -1 ? '皮肤电有所回落' : gsrDelta >= 1 ? '皮肤电有所升高' : '皮肤电变化不大'
  return `${stabilityText}，${hrText}，${gsrText}。`
}

function buildAdvice(value: MeditationMetrics) {
  if (value.signalQuality < 55) return '信号质量偏低：请减少动作，保持设备接触稳定。'
  if (value.betaTension >= 62) return 'Beta 偏高：请放松面部、肩颈和下颌，减少用力。'
  if (value.heartRate >= 88) return '心率偏高：可以放慢呼吸，延长呼气时间。'
  if (value.hrv < 34) return 'HRV 偏低：请保持稳定、缓慢、自然的呼吸节奏。'
  if (value.gsr >= 28) return 'EDA/GSR 偏高：可能处于较高唤醒状态，请减少动作并回到视频引导。'
  if (value.alphaRelaxation >= 66) return 'Alpha 提升：当前放松状态较好，请继续保持。'
  return '请保持舒适坐姿，跟随视频节奏自然呼吸。'
}

function currentActiveMs() {
  return activeMs.value + (running.value ? Date.now() - runStartedAtMs : 0)
}

function formatMetric(card: MetricCard) {
  const value = metrics.value[card.key]
  if (card.key === 'heartRate') return value.toFixed(0)
  if (card.key === 'gsr') return value.toFixed(1)
  return value.toFixed(1)
}

function formatDuration(seconds: number) {
  const minute = Math.floor(seconds / 60)
  const second = seconds % 60
  return `${minute}:${String(second).padStart(2, '0')}`
}

function average(values: number[]) {
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function standardDeviation(values: number[]) {
  const avg = average(values)
  return Math.sqrt(average(values.map((value) => (value - avg) ** 2)))
}

function round1(value: number) {
  return Math.round(value * 10) / 10
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

const guidanceText = '请保持舒适坐姿，放松肩颈和面部肌肉。跟随视频进行呼吸或正念练习，不需要刻意控制脑电或生理信号。系统会同步记录脑电、心率和皮肤电等状态变化，并生成本次练习报告。'
</script>

<template>
  <section class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-lg shadow-cyan-100/40 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none" data-testid="biosignal-meditation-demo">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="space-y-2">
        <div class="inline-flex items-center gap-2 rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700 dark:bg-teal-950/40 dark:text-teal-200">
          <Sparkles class="h-4 w-4" />
          脑机交互冥想
        </div>
        <h2 class="text-xl font-black text-slate-900 dark:text-white">视频引导 + 生理信号监测</h2>
        <p class="max-w-3xl text-sm leading-7 text-slate-500 dark:text-slate-300">{{ guidanceText }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
          <span class="h-2 w-2 rounded-full" :class="connected ? 'bg-emerald-500' : 'bg-slate-300'" />
          {{ statusText }}
        </span>
        <span class="rounded-xl bg-slate-50 px-3 py-2 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">{{ formatDuration(elapsedSeconds) }}</span>
      </div>
    </div>

    <div v-if="videoError" class="mt-4 rounded-2xl bg-amber-50 p-4 text-sm font-bold text-amber-700 dark:bg-amber-950/30 dark:text-amber-200">{{ videoError }}</div>
    <div v-if="gatewayError" class="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ gatewayError }}</div>
    <div v-if="saveError" class="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ saveError }}</div>
    <div v-else-if="savedReportId" class="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm font-bold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">
      冥想训练报告已保存。
      <button class="ml-2 underline" type="button" @click="router.push(`/brain-intervention/reports/${savedReportId}`)">查看报告</button>
    </div>

    <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div class="min-w-0 space-y-4">
        <div class="overflow-hidden rounded-3xl border border-slate-100 bg-black dark:border-slate-800">
          <div class="flex flex-col gap-3 bg-white p-4 dark:bg-slate-950 lg:flex-row lg:items-center lg:justify-between">
            <div class="min-w-0">
              <div class="flex items-center gap-2 text-xs font-bold text-slate-400">
                <Video class="h-4 w-4 text-teal-600" />
                当前视频
              </div>
              <p class="mt-1 truncate text-base font-black text-slate-900 dark:text-white">{{ selectedVideo?.title || '暂无可用视频' }}</p>
              <p class="mt-1 line-clamp-1 text-xs font-bold text-slate-400">
                {{ selectedVideo ? `约 ${Math.round(selectedVideo.durationSec / 60)} 分钟 · ${selectedVideo.description || '视频引导练习'}` : '请先选择冥想视频' }}
              </p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <Loader2 v-if="loadingVideos" class="h-4 w-4 animate-spin text-slate-400" />
              <select
                v-model="selectedVideoId"
                class="h-10 max-w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700 outline-none transition focus:border-teal-400 disabled:bg-slate-50 disabled:text-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:disabled:bg-slate-800"
                :disabled="running || savingReport || loadingVideos"
                aria-label="选择冥想视频"
              >
                <option v-for="video in videos" :key="video.id" :value="video.id">{{ video.title }}</option>
              </select>
            </div>
          </div>

          <video
            v-if="selectedVideo"
            ref="videoRef"
            class="aspect-video max-h-[64vh] min-h-[260px] w-full bg-black object-contain"
            :src="selectedVideo.url"
            controls
            playsinline
            preload="metadata"
            @ended="endSession"
            @error="videoError = '视频加载失败，请切换其他视频或稍后重试'"
          />
          <div v-else class="grid aspect-video min-h-[260px] place-items-center text-sm font-bold text-white/70">暂无可用视频</div>

          <div class="flex flex-col gap-3 bg-white p-4 dark:bg-slate-950 sm:flex-row sm:items-center sm:justify-between">
            <div class="flex flex-wrap gap-2">
              <button class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white disabled:bg-slate-200 disabled:text-slate-400 dark:bg-white dark:text-slate-900 dark:disabled:bg-slate-800" :disabled="!selectedVideo || savingReport" type="button" @click="running ? pauseSession() : startSession()">
                <Pause v-if="running" class="h-4 w-4" />
                <Play v-else class="h-4 w-4" />
                {{ running ? '暂停' : paused ? '继续' : completed ? '重新开始' : '开始' }}
              </button>
              <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-700 disabled:text-slate-300 dark:border-slate-700 dark:text-slate-200" :disabled="(!running && !paused) || savingReport" type="button" @click="endSession">
                <Square class="h-4 w-4" />
                结束
              </button>
              <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-500 dark:border-slate-700 dark:text-slate-300" :disabled="running || savingReport" type="button" @click="resetSession">
                重置
              </button>
            </div>
            <span v-if="connecting || savingReport" class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
              <Loader2 class="h-4 w-4 animate-spin" />
              {{ savingReport ? '保存报告' : '连接信号' }}
            </span>
          </div>
        </div>
      </div>

      <aside class="space-y-3">
        <div class="rounded-3xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-black text-slate-900 dark:text-white">综合冥想稳定度</p>
            <span class="text-xs font-bold text-slate-400">0-100</span>
          </div>
          <div class="mt-3 flex items-end gap-3">
            <p class="text-5xl font-black text-slate-900 dark:text-white">{{ metrics.stability.toFixed(0) }}</p>
            <p class="pb-2 text-sm font-bold text-slate-400">/ 100</p>
          </div>
          <div class="mt-4 h-3 overflow-hidden rounded-full bg-white dark:bg-slate-900">
            <div class="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 transition-all" :style="{ width: `${metrics.stability}%` }" />
          </div>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <p class="text-sm font-black text-slate-900 dark:text-white">实时建议</p>
          <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ advice }}</p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <article class="rounded-2xl border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
            <p class="text-[11px] font-bold text-slate-400">心率 HR</p>
            <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ metrics.heartRate.toFixed(0) }} <span class="text-xs text-slate-400">bpm</span></p>
          </article>
          <article class="rounded-2xl border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
            <p class="text-[11px] font-bold text-slate-400">HRV</p>
            <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ metrics.hrv.toFixed(1) }} <span class="text-xs text-slate-400">ms</span></p>
          </article>
          <article class="rounded-2xl border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
            <p class="text-[11px] font-bold text-slate-400">皮肤电</p>
            <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ metrics.gsr.toFixed(1) }} <span class="text-xs text-slate-400">mV</span></p>
          </article>
          <article class="rounded-2xl border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
            <p class="text-[11px] font-bold text-slate-400">信号质量</p>
            <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ metrics.signalQuality.toFixed(0) }} <span class="text-xs text-slate-400">%</span></p>
          </article>
        </div>

        <div class="rounded-3xl border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-black text-slate-900 dark:text-white">稳定度趋势</p>
              <p class="mt-1 text-xs font-bold text-slate-400">最近 {{ trend.length }} 个 500ms 点</p>
            </div>
            <TrendingUp class="h-5 w-5 text-teal-600" />
          </div>
          <svg class="mt-3 h-24 w-full" viewBox="0 0 320 96" preserveAspectRatio="none" role="img" :aria-label="trendLabel('冥想稳定度', trend.map(item => item.stability))">
            <line x1="0" y1="48" x2="320" y2="48" class="stroke-slate-100 dark:stroke-slate-800" stroke-width="1" />
            <polyline v-if="trendPoints" :points="trendPoints" fill="none" stroke="#0d9488" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" />
          </svg>
        </div>
      </aside>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
      <article v-for="card in detailMetricCards" :key="card.key" class="rounded-2xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-black text-slate-900 dark:text-white">{{ card.title }}</p>
            <p class="mt-1 text-[11px] font-bold text-slate-400">{{ card.range }}</p>
          </div>
          <div class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white dark:bg-slate-900" :style="{ color: card.color }">
            <component :is="card.icon" class="h-4 w-4" />
          </div>
        </div>
        <p class="mt-3 text-xl font-black text-slate-900 dark:text-white">{{ formatMetric(card) }} <span class="text-xs font-bold text-slate-400">{{ card.unit }}</span></p>
      </article>
    </div>
  </section>
</template>
