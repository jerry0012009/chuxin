<script setup lang="ts">
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Bluetooth,
  Brain,
  CheckCircle,
  Droplets,
  Heart,
  Lightbulb,
  Loader2,
  Moon,
  RefreshCw,
  Signal,
  Sparkles,
  Thermometer,
  Watch,
  X,
  Zap,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthSession } from '@/composables/useAuthSession'
import { getWearableDataByDateRange, upsertWearableData } from '@/db/api'
import type { BandConnectionStatus, SmartBandDevice, TimeRange, WearableData } from '@/types'

type HealthStatus = 'good' | 'warning' | 'attention'

interface HealthInsight {
  category: string
  status: HealthStatus
  score: number
  description: string
  recommendations: string[]
}

const router = useRouter()
const { state: authState, ensureInitialized } = useAuthSession()

const activeTab = ref<'overview' | 'charts' | 'ai'>('overview')
const timeRange = ref<TimeRange>('week')
const connectionDialogOpen = ref(false)
const wearableData = ref<WearableData[]>([])
const loading = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')
const toastMessage = computed(() => errorMessage.value || statusMessage.value)
const toastTone = computed(() => (errorMessage.value ? 'error' : 'success'))

const connectionStatus = ref<BandConnectionStatus>('disconnected')
const connectedDevice = ref<SmartBandDevice | null>(null)
const availableDevices = ref<SmartBandDevice[]>([])
const realtimeData = ref<Partial<WearableData> | null>(null)
const isScanning = ref(false)
const isConnecting = ref(false)
const connectionError = ref<string | null>(null)

let scanTimer: ReturnType<typeof setTimeout> | null = null
let connectTimer: ReturnType<typeof setTimeout> | null = null
let realtimeTimer: ReturnType<typeof setInterval> | null = null
let persistTimer: ReturnType<typeof setInterval> | null = null
let toastTimer: ReturnType<typeof setTimeout> | null = null
let hasPersistedCurrentSession = false

const huaweiBand10: SmartBandDevice = {
  id: 'huawei-band-10-fixed',
  name: '华为手环 10',
  manufacturer: 'Huawei',
  model: 'Band 10',
  rssi: -68,
}

const randomHuaweiDevicesPool: SmartBandDevice[] = [
  { id: 'huawei-band-9-001', name: '华为手环 9', manufacturer: 'Huawei', model: 'Band 9', rssi: -65 },
  { id: 'huawei-watch-fit-002', name: '华为 Watch Fit 3', manufacturer: 'Huawei', model: 'Watch Fit 3', rssi: -72 },
  { id: 'huawei-band-8-003', name: '华为手环 8', manufacturer: 'Huawei', model: 'Band 8', rssi: -80 },
  { id: 'huawei-watch-4-004', name: '华为 Watch 4', manufacturer: 'Huawei', model: 'Watch 4', rssi: -70 },
  { id: 'huawei-band-7-005', name: '华为手环 7', manufacturer: 'Huawei', model: 'Band 7', rssi: -85 },
  { id: 'huawei-watch-gt4-006', name: '华为 Watch GT 4', manufacturer: 'Huawei', model: 'Watch GT 4', rssi: -68 },
]

const sleepStageData = [
  { name: '深睡', value: 28, color: 'bg-indigo-600' },
  { name: '浅睡', value: 42, color: 'bg-indigo-400' },
  { name: 'REM', value: 20, color: 'bg-indigo-200' },
  { name: '清醒', value: 10, color: 'bg-slate-200' },
]

const tips = [
  '保持规律作息，让身心更健康',
  '每天步行30分钟，活力满满一整天',
  '深呼吸放松，缓解压力好方法',
  '充足睡眠是健康的基石',
  '多喝水，让身体保持最佳状态',
  '适度运动，心情更愉悦',
  '关注心率变化，了解身体状态',
  '良好的睡眠习惯，从今晚开始',
]

const todayData = computed(() => wearableData.value[wearableData.value.length - 1] || wearableData.value[0] || null)
const isConnected = computed(() => connectionStatus.value === 'connected')
const healthTip = computed(() => tips[Math.abs((todayData.value?.steps || 0) + wearableData.value.length) % tips.length])

const average = (selector: (item: WearableData) => number | null | undefined, fallback: number) => {
  const values = wearableData.value.map(selector).filter((value): value is number => typeof value === 'number' && !Number.isNaN(value))
  if (values.length === 0) return fallback
  return values.reduce((sum, item) => sum + item, 0) / values.length
}

const overviewMetrics = computed(() => [
  {
    label: '平均心率',
    value: Math.round(todayData.value?.heart_rate || average((item) => item.heart_rate, 79)),
    unit: 'bpm',
    icon: Heart,
    card: 'from-rose-50 via-rose-50 to-rose-100/30 border-rose-100/50',
    iconSurface: 'bg-rose-200/70 text-rose-500',
  },
  {
    label: '平均血氧',
    value: Math.round(todayData.value?.blood_oxygen || average((item) => item.blood_oxygen, 96)),
    unit: '%',
    icon: Droplets,
    card: 'from-blue-50 via-blue-50 to-blue-100/30 border-blue-100/50',
    iconSurface: 'bg-blue-200/70 text-blue-500',
  },
  {
    label: '总步数',
    value: Math.round(todayData.value?.steps || average((item) => item.steps, 3827)),
    unit: '',
    icon: Zap,
    card: 'from-amber-50 via-amber-50 to-amber-100/30 border-amber-100/50',
    iconSurface: 'bg-amber-200/70 text-amber-500',
  },
  {
    label: '平均睡眠',
    value: Number((todayData.value?.sleep_hours || average((item) => item.sleep_hours, 7.94)).toFixed(1)),
    unit: 'h',
    icon: Moon,
    card: 'from-indigo-50 via-indigo-50 to-indigo-100/30 border-indigo-100/50',
    iconSurface: 'bg-indigo-200/70 text-indigo-500',
  },
  {
    label: '平均压力',
    value: Math.round(todayData.value?.stress_level || average((item) => item.stress_level, 32)),
    unit: '',
    icon: Activity,
    card: 'from-purple-50 via-purple-50 to-purple-100/30 border-purple-100/50',
    iconSurface: 'bg-purple-200/70 text-purple-500',
  },
  {
    label: '平均体温',
    value: Number((todayData.value?.temperature || average((item) => item.temperature, 36.6)).toFixed(1)),
    unit: '°C',
    icon: Thermometer,
    card: 'from-teal-50 via-teal-50 to-teal-100/30 border-teal-100/50',
    iconSurface: 'bg-teal-200/70 text-teal-500',
  },
])

const healthScore = computed(() => {
  const sleep = average((item) => item.sleep_hours, 7.5)
  const stress = average((item) => item.stress_level, 35)
  const oxygen = average((item) => item.blood_oxygen, 97)
  return Math.max(60, Math.min(96, Math.round(70 + Math.min(12, sleep) + (oxygen - 95) * 2 - stress / 8)))
})

const getConnectionStatusColor = () => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'bg-emerald-500'
    case 'connecting':
    case 'scanning':
      return 'bg-amber-500'
    case 'connection_failed':
      return 'bg-rose-500'
    default:
      return 'bg-slate-400'
  }
}

const getConnectionStatusText = () => {
  switch (connectionStatus.value) {
    case 'connected':
      return connectedDevice.value?.name || '已连接'
    case 'connecting':
      return '连接中...'
    case 'scanning':
      return '扫描中...'
    case 'connection_failed':
      return '连接失败'
    default:
      return '未连接'
  }
}

const toDateKey = (date: Date) => date.toISOString().split('T')[0]!

const generateMockWearableData = (userId: string, startDate: Date, endDate: Date): WearableData[] => {
  const data: WearableData[] = []
  const currentDate = new Date(startDate)
  while (currentDate <= endDate) {
    const dateStr = toDateKey(currentDate)
    const sleepHours = 5.5 + Math.random() * 3
    data.push({
      id: `mock-${dateStr}`,
      user_id: userId,
      record_date: dateStr,
      heart_rate: Math.floor(65 + Math.random() * 20),
      sleep_hours: Number(sleepHours.toFixed(2)),
      sleep_quality: Math.floor(60 + Math.random() * 40),
      steps: Math.floor(3000 + Math.random() * 12000),
      calories: Math.floor(1500 + Math.random() * 800),
      stress_level: Math.floor(20 + Math.random() * 60),
      blood_oxygen: Math.floor(95 + Math.random() * 5),
      temperature: Number((36 + Math.random() * 1.5).toFixed(1)),
      data_json: {
        heart_rate_variability: Math.floor(20 + Math.random() * 40),
        deep_sleep_hours: Number((sleepHours * 0.2).toFixed(2)),
        rem_sleep_hours: Number((sleepHours * 0.25).toFixed(2)),
        awake_times: Math.floor(1 + Math.random() * 5),
      },
      created_at: currentDate.toISOString(),
    })
    currentDate.setDate(currentDate.getDate() + 1)
  }
  return data
}

const generateRealtimeMockData = (userId: string): Partial<WearableData> => ({
  user_id: userId,
  record_date: toDateKey(new Date()),
  heart_rate: Math.floor(60 + Math.random() * 40),
  blood_oxygen: Math.floor(95 + Math.random() * 5),
  steps: Math.floor(3000 + Math.random() * 8000),
  calories: Math.floor(50 + Math.random() * 200),
  stress_level: Math.floor(20 + Math.random() * 60),
  temperature: Number((36 + Math.random()).toFixed(1)),
})

const generateMockDeviceList = () => {
  const selected = [...randomHuaweiDevicesPool].sort(() => Math.random() - 0.5).slice(0, 3)
  return [huaweiBand10, ...selected]
}

const loadWearableData = async () => {
  await ensureInitialized()
  if (!authState.user?.id) return

  loading.value = true
  errorMessage.value = ''
  try {
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 30)
    const data = await getWearableDataByDateRange(authState.user.id, toDateKey(startDate), toDateKey(endDate))
    wearableData.value = data.length > 0 ? data : generateMockWearableData(authState.user.id, startDate, endDate)
  } catch {
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 30)
    wearableData.value = generateMockWearableData(authState.user.id, startDate, endDate)
  } finally {
    loading.value = false
  }
}

const scanDevices = () => {
  connectionError.value = null
  isScanning.value = true
  connectionStatus.value = 'scanning'
  if (scanTimer) clearTimeout(scanTimer)
  scanTimer = setTimeout(() => {
    availableDevices.value = generateMockDeviceList()
    statusMessage.value = `发现 ${availableDevices.value.length} 个设备`
    isScanning.value = false
    connectionStatus.value = 'disconnected'
  }, 800)
}

const persistRealtimeData = async () => {
  if (!authState.user?.id || !realtimeData.value) return
  await upsertWearableData({
    ...realtimeData.value,
    user_id: authState.user.id,
    record_date: realtimeData.value.record_date || toDateKey(new Date()),
  })
}

const connectDevice = (device: SmartBandDevice) => {
  if (!authState.user?.id) {
    connectionError.value = '请先登录'
    return
  }
  connectionError.value = null
  isConnecting.value = true
  connectionStatus.value = 'connecting'
  if (connectTimer) clearTimeout(connectTimer)
  connectTimer = setTimeout(() => {
    connectedDevice.value = device
    connectionStatus.value = 'connected'
    isConnecting.value = false
    hasPersistedCurrentSession = false
    statusMessage.value = `已连接到 ${device.name}`
    realtimeData.value = generateRealtimeMockData(authState.user!.id)
    realtimeTimer = setInterval(() => {
      realtimeData.value = {
        ...realtimeData.value,
        ...generateRealtimeMockData(authState.user!.id),
      }
    }, 3000)
    void persistRealtimeData().then(() => {
      hasPersistedCurrentSession = true
      void loadWearableData()
    })
    persistTimer = setInterval(() => {
      void persistRealtimeData()
    }, 60000)
  }, 1000)
}

const disconnectDevice = () => {
  if (realtimeTimer) clearInterval(realtimeTimer)
  if (persistTimer) clearInterval(persistTimer)
  realtimeTimer = null
  persistTimer = null
  connectedDevice.value = null
  connectionStatus.value = 'disconnected'
  realtimeData.value = null
  hasPersistedCurrentSession = false
  statusMessage.value = '已断开连接'
}

watch(realtimeData, () => {
  if (connectionStatus.value !== 'connected' || hasPersistedCurrentSession) return
  void persistRealtimeData().then(() => {
    hasPersistedCurrentSession = true
  })
})

const filteredTrendData = computed(() => {
  const days = timeRange.value === 'day' ? 1 : timeRange.value === 'week' ? 7 : 30
  return wearableData.value.slice(-days)
})

const chartRows = computed(() => [
  { key: 'heart_rate', title: '心率趋势', icon: Heart, color: 'bg-rose-500', unit: 'bpm', max: 120, values: filteredTrendData.value.map((item) => item.heart_rate || 70) },
  { key: 'sleep', title: '睡眠时长趋势', icon: Moon, color: 'bg-indigo-500', unit: 'h', max: 12, values: filteredTrendData.value.map((item) => item.sleep_hours || 7) },
  { key: 'steps', title: '步数统计', icon: Zap, color: 'bg-amber-500', unit: '', max: 15000, values: filteredTrendData.value.map((item) => item.steps || 5000) },
  { key: 'stress', title: '压力值趋势', icon: Activity, color: 'bg-purple-500', unit: '', max: 100, values: filteredTrendData.value.map((item) => item.stress_level || 35) },
  { key: 'temperature', title: '体温变化', icon: Thermometer, color: 'bg-teal-500', unit: '°C', max: 38, values: filteredTrendData.value.map((item) => item.temperature || 36.6) },
  { key: 'blood_oxygen', title: '血氧饱和度趋势', icon: Droplets, color: 'bg-blue-500', unit: '%', max: 100, values: filteredTrendData.value.map((item) => item.blood_oxygen || 97) },
])

const insights = computed<HealthInsight[]>(() => {
  if (wearableData.value.length === 0) return []
  const avgHeartRate = average((item) => item.heart_rate, 70)
  const avgSleep = average((item) => item.sleep_hours, 7)
  const avgStress = average((item) => item.stress_level, 40)
  const avgBloodOxygen = average((item) => item.blood_oxygen, 98)
  const results: HealthInsight[] = []

  results.push(
    avgHeartRate > 80
      ? {
          category: '心率健康',
          status: 'attention',
          score: 65,
          description: '您的平均心率略高，可能存在轻度焦虑或压力',
          recommendations: ['尝试深呼吸练习，每天3次，每次5分钟', '减少咖啡因摄入，避免午后饮用咖啡', '增加有氧运动，如快走、慢跑'],
        }
      : {
          category: '心率健康',
          status: 'good',
          score: 85,
          description: '您的心率处于正常范围，心脏健康状况良好',
          recommendations: ['保持当前的运动习惯', '继续监测心率变化'],
        },
  )

  results.push(
    avgSleep < 6
      ? {
          category: '睡眠质量',
          status: 'warning',
          score: 55,
          description: '您的睡眠时间不足，可能影响情绪和认知功能',
          recommendations: ['建立规律的作息时间，每天同一时间入睡和起床', '睡前1小时避免使用电子设备', '尝试冥想或放松练习帮助入睡'],
        }
      : avgSleep < 7
        ? {
            category: '睡眠质量',
            status: 'attention',
            score: 70,
            description: '您的睡眠时间略短，建议适当增加',
            recommendations: ['尝试提前30分钟入睡', '优化睡眠环境，保持安静和适宜温度'],
          }
        : {
            category: '睡眠质量',
            status: 'good',
            score: 90,
            description: '您的睡眠时长充足，有助于身心健康',
            recommendations: ['继续保持良好的睡眠习惯', '关注深度睡眠比例'],
          },
  )

  results.push(
    avgStress > 60
      ? {
          category: '压力水平',
          status: 'warning',
          score: 50,
          description: '您的压力水平较高，需要及时调节',
          recommendations: ['识别压力源，尝试解决问题或寻求帮助', '每天进行15-20分钟的正念冥想', '与亲友交流，分享您的感受', '必要时咨询专业心理咨询师'],
        }
      : avgStress > 40
        ? {
            category: '压力水平',
            status: 'attention',
            score: 70,
            description: '您的压力水平中等，注意适当放松',
            recommendations: ['安排一些休闲活动，如阅读、听音乐', '保持社交活动，与朋友聚会', '学习压力管理技巧'],
          }
        : {
            category: '压力水平',
            status: 'good',
            score: 88,
            description: '您的压力水平控制良好',
            recommendations: ['继续保持当前的生活节奏', '分享您的压力管理经验'],
          },
  )

  results.push(
    avgBloodOxygen < 95
      ? {
          category: '血氧饱和度',
          status: 'attention',
          score: 75,
          description: '您的血氧水平略低，建议关注呼吸健康',
          recommendations: ['保持室内通风良好', '进行深呼吸练习', '如持续偏低，建议咨询管理员'],
        }
      : {
          category: '血氧饱和度',
          status: 'good',
          score: 92,
          description: '您的血氧水平正常，呼吸系统健康',
          recommendations: ['继续保持良好的生活习惯', '适当进行有氧运动增强肺功能'],
        },
  )

  return results
})

const overallAiScore = computed(() => {
  if (insights.value.length === 0) return 0
  return Math.floor(insights.value.reduce((sum, item) => sum + item.score, 0) / insights.value.length)
})

const mentalHealthRisk = computed(() => {
  const avgStress = average((item) => item.stress_level, 40)
  const avgSleep = average((item) => item.sleep_hours, 7)
  const avgHeartRate = average((item) => item.heart_rate, 70)
  if (avgStress > 70 && avgSleep < 6) return { level: 'high' as const, score: 75, label: '高风险', color: 'bg-rose-500' }
  if (avgStress > 50 || avgSleep < 6.5 || avgHeartRate > 85) return { level: 'moderate' as const, score: 50, label: '中等风险', color: 'bg-amber-500' }
  return { level: 'low' as const, score: 25, label: '低风险', color: 'bg-emerald-500' }
})

const statusTone = (status: HealthStatus) => {
  if (status === 'good') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (status === 'warning') return 'border-amber-200 bg-amber-50 text-amber-700'
  return 'border-rose-200 bg-rose-50 text-rose-700'
}

watch(toastMessage, (message) => {
  if (toastTimer) clearTimeout(toastTimer)
  if (!message) return
  toastTimer = setTimeout(() => {
    statusMessage.value = ''
    errorMessage.value = ''
  }, 2200)
})

onMounted(() => {
  void loadWearableData()
})

onBeforeUnmount(() => {
  if (scanTimer) clearTimeout(scanTimer)
  if (connectTimer) clearTimeout(connectTimer)
  if (toastTimer) clearTimeout(toastTimer)
  disconnectDevice()
})
</script>

<template>
  <div class="bg-background pb-12">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-5 z-[80] w-[calc(100%-32px)] max-w-sm -translate-x-1/2 rounded-xl border px-4 py-3 text-sm font-medium shadow-xl backdrop-blur"
      :class="toastTone === 'error' ? 'border-rose-200 bg-white text-rose-600' : 'border-slate-200 bg-white text-slate-800'"
      data-testid="smartband-toast"
    >
      {{ toastMessage }}
    </div>

    <header class="relative overflow-hidden px-5 pb-6 pt-8 text-white">
      <div class="absolute inset-0 bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-700" />
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(34,211,238,0.35),transparent_34%),radial-gradient(circle_at_15%_80%,rgba(99,102,241,0.38),transparent_30%)]" />
      <div class="relative z-10 mx-auto max-w-md">
        <div class="mb-6 flex items-center justify-between">
          <button class="flex h-10 w-10 items-center justify-center rounded-full text-white transition hover:bg-white/20" @click="router.push('/profile')">
            <ArrowLeft class="h-5 w-5" />
          </button>
          <h1 class="text-lg font-bold">手环数据</h1>
          <button class="flex h-10 w-10 items-center justify-center rounded-full text-white transition hover:bg-white/20 disabled:opacity-60" :disabled="loading" @click="loadWearableData">
            <RefreshCw class="h-5 w-5" :class="loading ? 'animate-spin' : ''" />
          </button>
        </div>

        <button
          class="w-full rounded-2xl bg-white/10 p-4 text-left backdrop-blur-sm transition hover:bg-white/20"
          data-testid="smartband-connection-card"
          @click="connectionDialogOpen = true"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
                <Activity class="h-6 w-6 text-white" />
              </div>
              <div>
                <p class="font-medium text-white">智能手环</p>
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full" :class="getConnectionStatusColor()" />
                  <span class="text-sm text-white/80">{{ getConnectionStatusText() }}</span>
                </div>
              </div>
            </div>
            <Bluetooth class="h-5 w-5 text-white/60" />
          </div>

          <div v-if="isConnected && realtimeData" class="mt-4 border-t border-white/20 pt-4" data-testid="smartband-realtime-preview">
            <div class="grid grid-cols-4 gap-2 text-center">
              <div>
                <p class="text-xs text-white/60">心率</p>
                <p class="text-lg font-medium text-white">{{ realtimeData.heart_rate || '--' }}</p>
              </div>
              <div>
                <p class="text-xs text-white/60">血氧</p>
                <p class="text-lg font-medium text-white">{{ realtimeData.blood_oxygen || '--' }}%</p>
              </div>
              <div>
                <p class="text-xs text-white/60">压力</p>
                <p class="text-lg font-medium text-white">{{ realtimeData.stress_level || '--' }}</p>
              </div>
              <div>
                <p class="text-xs text-white/60">体温</p>
                <p class="text-lg font-medium text-white">{{ realtimeData.temperature || '--' }}°C</p>
              </div>
            </div>
          </div>
        </button>
      </div>
    </header>

    <main class="mx-auto mt-6 max-w-md px-4">
      <div class="mb-6 grid h-14 grid-cols-3 rounded-2xl bg-white/80 p-1.5 shadow-md backdrop-blur-sm dark:bg-slate-900/80">
        <button
          v-for="tab in [
            { id: 'overview', label: '数据概览', active: 'from-blue-500 to-cyan-500' },
            { id: 'charts', label: '趋势图表', active: 'from-purple-500 to-pink-500' },
            { id: 'ai', label: 'AI评估', active: 'from-emerald-500 to-teal-500' },
          ]"
          :key="tab.id"
          class="rounded-xl text-base font-medium transition-all"
          :class="activeTab === tab.id ? `bg-gradient-to-r ${tab.active} text-white shadow-lg` : 'text-slate-500'"
          :data-testid="`smartband-tab-${tab.id}`"
          @click="activeTab = tab.id as typeof activeTab"
        >
          {{ tab.label }}
        </button>
      </div>

      <section v-if="activeTab === 'overview'" class="space-y-4">
        <div v-if="loading" class="flex items-center justify-center py-8">
          <Loader2 class="h-6 w-6 animate-spin text-slate-400" />
        </div>
        <template v-else-if="wearableData.length > 0">
          <div class="rounded-3xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 p-6 text-white shadow-lg" data-testid="smartband-health-score">
            <div class="flex items-center justify-between">
              <div>
                <p class="mb-1 text-sm text-white/80">今日健康评分</p>
                <p class="text-5xl font-black">{{ healthScore }}</p>
                <p class="mt-2 text-xs text-white/70">您的状态很棒，继续保持！</p>
              </div>
              <div class="relative h-24 w-24">
                <svg class="h-24 w-24 -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,0.2)" stroke-width="8" fill="none" />
                  <circle cx="48" cy="48" r="40" stroke="white" stroke-width="8" fill="none" :stroke-dasharray="`${2 * Math.PI * 40 * (healthScore / 100)} ${2 * Math.PI * 40 * (1 - healthScore / 100)}`" stroke-linecap="round" />
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xl font-bold">{{ healthScore }}%</span>
                </div>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div v-for="item in overviewMetrics" :key="item.label" class="rounded-2xl border bg-gradient-to-br p-4 shadow-sm" :class="item.card">
              <div class="mb-3 flex items-center gap-2">
                <div class="flex h-9 w-9 items-center justify-center rounded-xl shadow-sm" :class="item.iconSurface">
                  <component :is="item.icon" class="h-5 w-5" />
                </div>
                <span class="text-sm font-medium text-slate-600">{{ item.label }}</span>
              </div>
              <p class="text-3xl font-semibold tracking-tight text-slate-800">
                {{ item.value }}<span class="ml-1 text-base font-normal text-slate-400/80">{{ item.unit }}</span>
              </p>
            </div>
          </div>

          <div class="py-4 text-center">
            <p class="text-sm italic text-slate-500">💡 {{ healthTip }}</p>
          </div>
        </template>
        <div v-else class="py-8 text-center text-slate-400">
          <p>暂无数据</p>
          <p class="text-sm">连接手环设备开始同步</p>
        </div>
      </section>

      <section v-else-if="activeTab === 'charts'" class="space-y-4" data-testid="smartband-charts">
        <div class="grid grid-cols-2 rounded-xl bg-white p-1 shadow-sm dark:bg-slate-900">
          <button class="rounded-lg px-3 py-2 text-sm font-semibold" :class="timeRange === 'week' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500'" @click="timeRange = 'week'">本周</button>
          <button class="rounded-lg px-3 py-2 text-sm font-semibold" :class="timeRange === 'month' ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500'" @click="timeRange = 'month'">本月</button>
        </div>

        <div v-for="row in chartRows" :key="row.key" class="rounded-2xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 class="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            <component :is="row.icon" class="h-4 w-4" />
            {{ row.title }}
          </h3>
          <div class="mt-4 flex h-32 items-end gap-1">
            <div v-for="(value, index) in row.values" :key="index" class="flex flex-1 flex-col items-center gap-1">
              <div class="w-full rounded-t" :class="row.color" :style="{ height: `${Math.max(8, Math.min(100, (Number(value) / row.max) * 100))}%` }" />
            </div>
          </div>
        </div>

        <div class="rounded-2xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 class="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            <Moon class="h-4 w-4 text-indigo-500" />
            睡眠阶段分布
          </h3>
          <div class="mt-4 flex h-8 overflow-hidden rounded-full">
            <div v-for="stage in sleepStageData" :key="stage.name" :class="stage.color" :style="{ width: `${stage.value}%` }" />
          </div>
          <div class="mt-3 flex justify-center gap-3">
            <div v-for="stage in sleepStageData" :key="stage.name" class="flex items-center gap-1">
              <span class="h-2 w-2 rounded-full" :class="stage.color" />
              <span class="text-xs text-slate-600">{{ stage.name }}</span>
            </div>
          </div>
        </div>
      </section>

      <section v-else class="space-y-4" data-testid="smartband-ai">
        <div v-if="wearableData.length === 0" class="rounded-2xl bg-white p-8 text-center shadow-sm dark:bg-slate-900">
          <Brain class="mx-auto mb-4 h-12 w-12 text-slate-300" />
          <p class="text-slate-500">暂无足够数据进行AI评估</p>
          <p class="mt-1 text-sm text-slate-400">请连接手环设备并同步数据</p>
        </div>

        <template v-else>
          <div class="rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-6 text-white shadow-lg">
            <div class="mb-4 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
                  <Brain class="h-6 w-6" />
                </div>
                <div>
                  <h3 class="text-lg font-bold">AI 心理健康评估</h3>
                  <p class="text-sm text-white/70">基于生理数据的智能分析</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-4xl font-black">{{ overallAiScore }}</p>
                <p class="text-xs text-white/70">综合评分</p>
              </div>
            </div>

            <div class="rounded-xl bg-white/10 p-4 backdrop-blur-sm">
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm font-medium">抑郁风险指数</span>
                <span class="rounded-full px-3 py-1 text-xs font-bold text-white" :class="mentalHealthRisk.color">{{ mentalHealthRisk.label }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-white/20">
                <div class="h-full rounded-full" :class="mentalHealthRisk.color" :style="{ width: `${mentalHealthRisk.score}%` }" />
              </div>
              <p class="mt-2 text-xs text-white/70">
                {{ mentalHealthRisk.level === 'high' ? '您的生理指标显示较高的心理压力，建议及时寻求专业帮助' : mentalHealthRisk.level === 'moderate' ? '您的压力水平中等，建议关注心理健康并进行适当调节' : '您的心理健康状况良好，继续保持！' }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <h4 class="flex items-center gap-2 font-medium text-slate-700">
              <Sparkles class="h-4 w-4 text-amber-500" />
              健康洞察与建议
            </h4>
            <article v-for="insight in insights" :key="insight.category" class="rounded-2xl border p-4" :class="statusTone(insight.status)">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <CheckCircle v-if="insight.status === 'good'" class="h-5 w-5 text-emerald-500" />
                  <AlertTriangle v-else-if="insight.status === 'warning'" class="h-5 w-5 text-amber-500" />
                  <Heart v-else class="h-5 w-5 text-rose-500" />
                  <h5 class="font-bold">{{ insight.category }}</h5>
                </div>
                <span class="text-lg font-bold">{{ insight.score }}分</span>
              </div>
              <p class="mt-3 text-sm">{{ insight.description }}</p>
              <div class="mt-3 space-y-2">
                <div class="flex items-center gap-2 text-sm font-medium">
                  <Lightbulb class="h-4 w-4" />
                  改善建议
                </div>
                <ul class="space-y-1.5">
                  <li v-for="item in insight.recommendations" :key="item" class="flex items-start gap-2 text-sm">
                    <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
                    {{ item }}
                  </li>
                </ul>
              </div>
            </article>
          </div>

          <div class="rounded-xl bg-slate-50 p-4 text-center text-xs text-slate-400">
            <p>AI评估结果仅供参考，不能替代专业医疗诊断</p>
            <p>如有健康疑虑，请咨询专业管理员</p>
          </div>
        </template>
      </section>
    </main>

    <div v-if="connectionDialogOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4" data-testid="smartband-dialog">
      <section class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2">
            <div class="flex h-8 w-8 items-center justify-center rounded-lg" :class="connectionStatus === 'connected' ? 'bg-emerald-50 text-emerald-500' : connectionStatus === 'scanning' ? 'bg-blue-50 text-blue-500' : 'bg-slate-50 text-slate-500'">
              <Bluetooth class="h-4 w-4" />
            </div>
            <div>
              <h2 class="font-bold text-slate-900 dark:text-white">连接智能手环</h2>
              <p class="text-xs text-slate-400">扫描附近可连接的智能手环</p>
            </div>
          </div>
          <button class="rounded-full p-1 text-slate-400 hover:bg-slate-100" @click="connectionDialogOpen = false">
            <X class="h-5 w-5" />
          </button>
        </div>

        <div class="mt-4 space-y-4">
          <div class="rounded-xl border border-current/20 p-4" :class="connectionStatus === 'connected' ? 'bg-emerald-50 text-emerald-500' : connectionStatus === 'scanning' ? 'bg-blue-50 text-blue-500' : connectionStatus === 'connecting' ? 'bg-amber-50 text-amber-500' : 'bg-slate-50 text-slate-500'">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <Signal class="h-5 w-5" />
                <div>
                  <p class="font-medium">{{ connectionStatus === 'connected' ? '已连接' : connectionStatus === 'connecting' ? '连接中...' : connectionStatus === 'scanning' ? '扫描中...' : '未连接' }}</p>
                  <p v-if="connectedDevice" class="text-xs opacity-80">{{ connectedDevice.name }}</p>
                </div>
              </div>
              <button v-if="connectionStatus === 'connected'" class="text-sm font-semibold text-rose-500" data-testid="smartband-disconnect" @click="disconnectDevice">断开</button>
            </div>
          </div>

          <div v-if="connectionError" class="rounded-lg border border-rose-100 bg-rose-50 p-3 text-sm text-rose-600">{{ connectionError }}</div>

          <button v-if="connectionStatus !== 'connected'" class="flex w-full items-center justify-center rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white disabled:opacity-60" :disabled="isScanning || isConnecting" data-testid="smartband-scan" @click="scanDevices">
            <Loader2 v-if="isScanning" class="mr-2 h-4 w-4 animate-spin" />
            <RefreshCw v-else class="mr-2 h-4 w-4" />
            {{ isScanning ? '扫描中...' : '扫描设备' }}
          </button>

          <div v-if="availableDevices.length > 0 && connectionStatus !== 'connected'" class="space-y-2">
            <p class="text-sm font-medium text-slate-600">可用设备</p>
            <div class="max-h-52 space-y-2 overflow-y-auto">
              <button
                v-for="device in availableDevices"
                :key="device.id"
                class="flex w-full items-center justify-between rounded-xl border border-slate-200 p-3 text-left transition hover:border-blue-300 hover:bg-blue-50/50"
                data-testid="smartband-device"
                @click="connectDevice(device)"
              >
                <span class="flex items-center gap-3">
                  <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500">
                    <Watch class="h-5 w-5 text-white" />
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ device.name }}</span>
                    <span class="text-xs text-slate-500">{{ device.manufacturer }} {{ device.model }}</span>
                  </span>
                </span>
                <span class="flex items-center gap-2">
                  <span v-if="device.rssi" class="text-xs text-slate-400">{{ device.rssi > -70 ? '信号强' : device.rssi > -85 ? '信号中' : '信号弱' }}</span>
                  <Loader2 v-if="isConnecting" class="h-4 w-4 animate-spin text-blue-500" />
                  <span v-else class="text-sm text-primary">连接</span>
                </span>
              </button>
            </div>
          </div>

          <div v-if="connectionStatus === 'connected' && connectedDevice" class="rounded-xl border border-emerald-100 bg-emerald-50 p-4" data-testid="smartband-connected-panel">
            <div class="flex items-center gap-3">
              <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
                <Watch class="h-6 w-6 text-white" />
              </div>
              <div>
                <p class="font-medium">{{ connectedDevice.name }}</p>
                <p class="text-xs text-emerald-600">设备已连接，正在同步数据</p>
              </div>
            </div>
          </div>

          <p class="text-center text-xs text-slate-400">请确保您的手环已开启蓝牙并处于可发现模式</p>
        </div>
      </section>
    </div>
  </div>
</template>
