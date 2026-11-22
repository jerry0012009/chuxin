<script setup lang="ts">
import { Activity, AlertTriangle, Bell, Brain, TrendingUp, Users } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { getAllAssessments, getAllEmotionDiaries, getAllProfiles, getRiskAlerts } from '@/db/api'
import type { Assessment, EmotionDiary, Profile, RiskAlert } from '@/types'

const loading = ref(true)
const errorMessage = ref('')
const profiles = ref<Profile[]>([])
const alerts = ref<RiskAlert[]>([])
const assessments = ref<Assessment[]>([])
const diaries = ref<EmotionDiary[]>([])
let toastTimer: number | null = null

watch(errorMessage, (message) => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  if (!message) {
    toastTimer = null
    return
  }
  toastTimer = window.setTimeout(() => {
    errorMessage.value = ''
    toastTimer = null
  }, 2200)
})

const emotionScores: Record<EmotionDiary['emotion_level'], number> = {
  very_bad: 1,
  bad: 2,
  neutral: 3,
  good: 4,
  very_good: 5,
}

const patients = computed(() => profiles.value.filter((item) => item.role === 'user'))
const profileMap = computed(() => new Map(profiles.value.map((item) => [item.id, item])))

const todayKey = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const overviewCards = computed(() => {
  const todayAssessments = assessments.value.filter((item) => item.created_at.slice(0, 10) === todayKey()).length
  const averageScore =
    diaries.value.length > 0
      ? diaries.value.reduce((sum, item) => sum + emotionScores[item.emotion_level], 0) / diaries.value.length
      : 0

  return [
    { label: '患者总数', value: `${patients.value.length}`, subtext: '已建档用户', icon: Users, tone: 'from-primary to-info' },
    { label: '待处理预警', value: `${alerts.value.length}`, subtext: '高风险优先处理', icon: Bell, tone: 'from-rose-500 to-orange-500' },
    { label: '今日评估', value: `${todayAssessments}`, subtext: '当天创建记录', icon: Brain, tone: 'from-cyan-500 to-blue-500' },
    { label: '平均情绪', value: averageScore ? averageScore.toFixed(1) : '0.0', subtext: '近全部日记 / 满分 5', icon: Activity, tone: 'from-emerald-500 to-teal-500' },
  ]
})

const riskSummary = computed(() => {
  const high = alerts.value.filter((item) => item.risk_level >= 8).length
  const medium = alerts.value.filter((item) => item.risk_level >= 5 && item.risk_level < 8).length
  const stable = Math.max(0, patients.value.length - high - medium)
  return { high, medium, stable }
})

const recentAlerts = computed(() =>
  alerts.value.slice(0, 3).map((item) => ({
    ...item,
    patientName: profileMap.value.get(item.patient_id)?.full_name || profileMap.value.get(item.patient_id)?.username || item.patient_id,
  })),
)

const patientRiskDistribution = computed(() => {
  const latestAssessmentMap = new Map<string, Assessment>()
  assessments.value.forEach((item) => {
    const current = latestAssessmentMap.get(item.user_id)
    if (!current || new Date(item.created_at).getTime() > new Date(current.created_at).getTime()) {
      latestAssessmentMap.set(item.user_id, item)
    }
  })

  return patients.value
    .map((patient) => {
      const patientAlerts = alerts.value.filter((item) => item.patient_id === patient.id)
      const highestAlert = patientAlerts.reduce((current, item) => Math.max(current, item.risk_level), 0)
      const latestAssessment = latestAssessmentMap.get(patient.id)
      const score = latestAssessment ? Number(latestAssessment.score ?? 0) : 0
      return {
        id: patient.id,
        name: patient.full_name || patient.username,
        summary: patientAlerts[0]?.description || '暂无风险摘要',
        adherence: latestAssessment ? Math.max(45, Math.min(96, 100 - Math.round(score / 2))) : 0,
      }
    })
    .slice(0, 8)
})

const emotionTrend = computed(() => {
  const grouped = new Map<string, number[]>()
  diaries.value.forEach((item) => {
    const key = item.diary_date
    grouped.set(key, [...(grouped.get(key) || []), emotionScores[item.emotion_level]])
  })

  return Array.from({ length: 7 }, (_, offset) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - offset))
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    const scores = grouped.get(key) || []
    const value = scores.length > 0 ? Number((scores.reduce((sum, item) => sum + item, 0) / scores.length).toFixed(1)) : 0
    return {
      key,
      label: `${date.getMonth() + 1}/${date.getDate()}`,
      value,
      percent: `${Math.max(10, (value / 5) * 100)}%`,
    }
  })
})

const assessmentDistribution = computed(() => {
  const counter = new Map<string, number>()
  assessments.value.forEach((item) => {
    const type = `${item.assessment_type || ''}`.toLowerCase()
    let label = '其他评估'
    if (type.includes('voice') || item.report?.voiceData) label = '语音情绪'
    else if (type.includes('expression') || type.includes('face') || item.report?.expressionData) label = '表情识别'
    else if (type.includes('htp')) label = '房树人评估'
    else if (type.includes('fusion') || type.includes('multimodal')) label = 'AI多模态报告'
    else if (type.includes('scale') || item.report?.scaleData) label = '量表评估'
    counter.set(label, (counter.get(label) || 0) + 1)
  })
  return Array.from(counter.entries()).map(([label, value]) => ({ label, value }))
})

const loadDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextProfiles, nextAlerts, nextAssessments, nextDiaries] = await Promise.all([
      getAllProfiles(),
      getRiskAlerts(false),
      getAllAssessments(),
      getAllEmotionDiaries(),
    ])
    profiles.value = nextProfiles
    alerts.value = nextAlerts
    assessments.value = nextAssessments
    diaries.value = nextDiaries
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载数据看板失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDashboard()
})

onUnmounted(() => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="space-y-6">
    <Transition name="toast-slide">
      <div
        v-if="errorMessage"
        data-testid="doctor-dashboard-toast"
        class="fixed left-1/2 top-6 z-[80] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full bg-rose-600 px-5 py-3 text-sm font-medium text-white shadow-xl shadow-rose-900/20"
      >
        {{ errorMessage }}
      </div>
    </Transition>

    <SectionTitle title="管理员数据看板" description="集中查看患者概况、预警状态、评估活跃度与情绪趋势。" />

    <div class="overflow-hidden rounded-[32px] bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 p-6 text-white">
      <div class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <p class="text-sm text-white/60">Clinical Overview</p>
          <h2 class="mt-2 text-3xl font-bold">实时监控患者健康状况</h2>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-white/75">
            实时汇总患者风险、评估活跃度与近期情绪趋势，帮助快速定位需要跟进的个案。
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-[24px] bg-white/10 p-4">
            <p class="text-xs text-white/60">高风险</p>
            <p class="mt-2 text-2xl font-bold">{{ riskSummary.high }}</p>
          </div>
          <div class="rounded-[24px] bg-white/10 p-4">
            <p class="text-xs text-white/60">中风险</p>
            <p class="mt-2 text-2xl font-bold">{{ riskSummary.medium }}</p>
          </div>
          <div class="rounded-[24px] bg-white/10 p-4">
            <p class="text-xs text-white/60">稳定患者</p>
            <p class="mt-2 text-2xl font-bold">{{ riskSummary.stable }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <BaseCard v-for="item in overviewCards" :key="item.label" class="glass border-white/60">
        <div class="flex items-center justify-between">
          <p class="text-sm text-slate-500">{{ item.label }}</p>
          <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br text-white" :class="item.tone">
            <component :is="item.icon" class="h-5 w-5" />
          </div>
        </div>
        <p class="mt-4 text-3xl font-bold text-slate-900 dark:text-white">{{ loading ? '...' : item.value }}</p>
        <p class="mt-2 text-xs text-slate-400">{{ item.subtext }}</p>
      </BaseCard>
    </div>

    <div class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <BaseCard>
        <SectionTitle title="患者风险分布" description="按最新评估和当前预警汇总患者随访优先级。" />
        <div v-if="loading" class="mt-6 text-sm text-slate-500">正在加载患者分布...</div>
        <div v-else class="mt-6 space-y-5">
          <div v-for="item in patientRiskDistribution" :key="item.id">
            <div class="mb-2 flex items-center justify-between gap-4 text-sm">
              <span class="font-medium text-slate-700 dark:text-slate-200">{{ item.name }}</span>
              <span class="truncate text-slate-400">{{ item.summary }}</span>
            </div>
            <ProgressBar :value="item.adherence" />
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle title="最近预警" description="优先关注最新未处理预警。" />
        <div v-if="loading" class="mt-5 text-sm text-slate-500">正在加载预警...</div>
        <div v-else-if="recentAlerts.length === 0" class="mt-5 rounded-[24px] bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900">
          当前没有待处理预警。
        </div>
        <div v-else class="mt-5 space-y-3">
          <div v-for="item in recentAlerts" :key="item.id" class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
            <div class="flex items-center gap-3">
              <AlertTriangle class="h-5 w-5 text-rose-500" />
              <p class="font-semibold text-slate-900 dark:text-white">{{ item.patientName }}</p>
            </div>
            <p class="mt-2 text-sm text-slate-500">{{ item.alert_type }} · 风险 {{ item.risk_level }}/10</p>
            <p class="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">{{ item.description }}</p>
          </div>
        </div>
      </BaseCard>
    </div>

    <div class="grid gap-6 lg:grid-cols-2">
      <BaseCard>
        <SectionTitle title="近 7 日情绪趋势" description="按日记情绪值换算为 1-5 分的平均曲线。" />
        <div v-if="loading" class="mt-5 text-sm text-slate-500">正在计算趋势...</div>
        <div v-else class="mt-5">
          <div class="flex h-56 items-end gap-3">
            <div v-for="item in emotionTrend" :key="item.key" class="flex flex-1 flex-col items-center gap-3">
              <div class="flex h-44 w-full items-end rounded-[16px] bg-slate-50 p-2 dark:bg-slate-900">
                <div class="w-full rounded-[12px] bg-gradient-to-t from-primary to-info" :style="{ height: item.percent }" />
              </div>
              <div class="text-center">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">{{ item.value.toFixed(1) }}</p>
                <p class="text-xs text-slate-400">{{ item.label }}</p>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle title="评估类型分布" description="从当前 assessments 实际数据汇总评估类型。" />
        <div v-if="loading" class="mt-5 text-sm text-slate-500">正在汇总评估...</div>
        <div v-else-if="assessmentDistribution.length === 0" class="mt-5 rounded-[24px] bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900">
          当前没有评估数据。
        </div>
        <div v-else class="mt-5 space-y-4">
          <div v-for="item in assessmentDistribution" :key="item.label" class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
            <div class="mb-2 flex items-center justify-between">
              <span class="font-semibold text-slate-900 dark:text-white">{{ item.label }}</span>
              <span class="text-sm text-slate-500">{{ item.value }}</span>
            </div>
            <ProgressBar :value="Math.min(100, (item.value / Math.max(1, assessments.length)) * 100)" />
          </div>
        </div>
      </BaseCard>
    </div>

    <BaseCard>
      <SectionTitle title="今日重点" description="根据预警与知识更新状态提示管理员优先动作。" />
      <div class="mt-5 grid gap-3 md:grid-cols-2">
        <div class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
          <div class="flex items-center gap-3">
            <AlertTriangle class="h-5 w-5 text-rose-500" />
            <p class="font-semibold text-slate-900 dark:text-white">优先联系高风险患者</p>
          </div>
          <p class="mt-2 text-sm text-slate-500">
            当前共有 {{ alerts.length }} 条待处理预警，其中高风险 {{ riskSummary.high }} 条。
          </p>
        </div>
        <div class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
          <div class="flex items-center gap-3">
            <TrendingUp class="h-5 w-5 text-primary" />
            <p class="font-semibold text-slate-900 dark:text-white">关注近期评估活跃度</p>
          </div>
          <p class="mt-2 text-sm text-slate-500">
            今日新增评估 {{ overviewCards[2]?.value || 0 }} 条，建议结合疗愈执行情况安排复评。
          </p>
        </div>
      </div>
    </BaseCard>
  </div>
</template>
