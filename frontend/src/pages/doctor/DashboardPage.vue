<script setup lang="ts">
import { ArrowRight, CheckCircle2 } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import { assessmentTypeLabel } from '@/lib/assessment-display'
import { getAllAssessments, getAllEmotionDiaries, getAllProfiles, getRiskAlerts } from '@/db/api'
import type { Assessment, EmotionDiary, Profile, RiskAlert } from '@/types'

const loading = ref(true)
const loadFailed = ref(false)
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

const todayAssessments = computed(() => assessments.value.filter((item) => item.created_at.slice(0, 10) === todayKey()).length)
const overviewMetrics = computed(() => {
  const averageScore =
    diaries.value.length > 0
      ? diaries.value.reduce((sum, item) => sum + emotionScores[item.emotion_level], 0) / diaries.value.length
      : null

  return [
    { label: '参与者总数', value: `${patients.value.length}`, unit: '人', subtext: '当前可见的普通账户' },
    { label: '今日评估', value: `${todayAssessments.value}`, unit: '条', subtext: '按记录日期统计' },
    { label: '平均情绪', value: averageScore?.toFixed(1) ?? '—', unit: averageScore === null ? '' : '/ 5', subtext: averageScore === null ? '暂无日记' : '最近最多 1000 条日记' },
  ]
})

const riskSummary = computed(() => {
  const high = alerts.value.filter((item) => item.risk_level >= 8).length
  const medium = alerts.value.filter((item) => item.risk_level >= 5 && item.risk_level < 8).length
  return { high, medium, other: alerts.value.length - high - medium }
})

const priorityAlerts = computed(() =>
  [...alerts.value].sort((a, b) => b.risk_level - a.risk_level || b.created_at.localeCompare(a.created_at)).slice(0, 3).map((item) => ({
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
      const latestAssessment = latestAssessmentMap.get(patient.id)
      const report = latestAssessment?.report
      const summary = [report?.overall?.summary, report?.summary, ...patientAlerts.map((alert) => alert.description)]
        .find((value): value is string => typeof value === 'string' && value.trim().length > 0)
      return {
        id: patient.id,
        name: patient.full_name || patient.username,
        assessment: latestAssessment,
        summary,
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
    const value = scores.length > 0 ? Number((scores.reduce((sum, item) => sum + item, 0) / scores.length).toFixed(1)) : null
    return {
      key,
      label: `${date.getMonth() + 1}/${date.getDate()}`,
      value,
      percent: `${((value ?? 0) / 5) * 100}%`,
    }
  })
})

const assessmentDistribution = computed(() => {
  const counter = new Map<string, number>()
  assessments.value.forEach((item) => {
    const label = assessmentTypeLabel(item)
    counter.set(label, (counter.get(label) || 0) + 1)
  })
  return Array.from(counter.entries()).map(([label, value]) => ({ label, value }))
})

const loadDashboard = async () => {
  loading.value = true
  loadFailed.value = false
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
    loadFailed.value = true
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
  <div class="dashboard">
    <Transition name="toast-slide">
      <div
        v-if="errorMessage"
        data-testid="doctor-dashboard-toast"
        class="fixed left-1/2 top-6 z-[80] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full bg-rose-600 px-5 py-3 text-sm font-medium text-white shadow-xl shadow-rose-900/20"
      >
        {{ errorMessage }}
      </div>
    </Transition>

    <header class="dashboard-title"><h1>数据看板</h1><p>参与者评估与预警概况</p></header>
    <p v-if="loadFailed" class="service-card p-4 text-sm" role="alert">看板数据暂时无法加载。 <button class="service-link" type="button" @click="loadDashboard">重试</button></p>
    <template v-else>

    <div class="dashboard-operations">
      <section class="dashboard-queue" aria-labelledby="pending-risk-title">
        <header class="dashboard-section-head">
          <div><h2 id="pending-risk-title">待处理预警</h2><p>{{ loading ? '正在加载预警…' : `共 ${alerts.length} 条 · 按风险从高到低` }}</p></div>
          <RouterLink to="/admin/alerts" class="dashboard-link service-link">查看预警 <ArrowRight aria-hidden="true" /></RouterLink>
        </header>
        <dl class="dashboard-risks">
          <div><dt>高风险</dt><dd :class="{ 'risk-high': riskSummary.high > 0 }">{{ loading ? '…' : `${riskSummary.high} 条` }}</dd></div>
          <div><dt>中风险</dt><dd>{{ loading ? '…' : `${riskSummary.medium} 条` }}</dd></div>
          <div><dt>其他预警</dt><dd>{{ loading ? '…' : `${riskSummary.other} 条` }}</dd></div>
        </dl>
        <p v-if="!loading && !priorityAlerts.length" class="dashboard-queue-empty"><CheckCircle2 aria-hidden="true" /> 当前没有待处理预警。</p>
        <ul v-else-if="priorityAlerts.length" class="dashboard-alerts" aria-label="优先处理的预警">
          <li v-for="item in priorityAlerts" :key="item.id">
            <div class="dashboard-alert-head">
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.alert_type }}</span>
              <ServiceStatus :tone="item.risk_level >= 8 ? 'danger' : item.risk_level >= 5 ? 'attention' : 'idle'">风险 {{ item.risk_level }} / 10</ServiceStatus>
            </div>
            <p>{{ item.description }}</p>
          </li>
        </ul>
      </section>
      <section class="dashboard-metrics" aria-labelledby="dashboard-metrics-title">
        <h2 id="dashboard-metrics-title">数据概况</h2>
        <dl>
          <div v-for="item in overviewMetrics" :key="item.label" class="dashboard-metric">
            <dt>{{ item.label }}<span>{{ item.subtext }}</span></dt>
            <dd>{{ loading ? '…' : item.value }} <small v-if="!loading">{{ item.unit }}</small></dd>
          </div>
        </dl>
      </section>
    </div>

    <section class="dashboard-participants" aria-labelledby="dashboard-participants-title">
      <header class="dashboard-section-head">
        <div><h2 id="dashboard-participants-title">参与者评估与风险摘要</h2><p>最近一次可见评估 · 最多显示 8 人</p></div>
        <RouterLink to="/admin/patients" class="dashboard-link service-link">参与者管理 <ArrowRight aria-hidden="true" /></RouterLink>
      </header>
      <p v-if="loading" class="dashboard-empty" role="status">正在加载参与者数据…</p>
      <p v-else-if="!patientRiskDistribution.length" class="dashboard-empty">暂无参与者。</p>
      <table v-else class="dashboard-table" role="table" aria-labelledby="dashboard-participants-title">
        <thead role="rowgroup"><tr role="row"><th role="columnheader" scope="col">参与者</th><th role="columnheader" scope="col">状态</th><th role="columnheader" scope="col">评估类型</th><th role="columnheader" scope="col">总分</th><th role="columnheader" scope="col">风险摘要</th></tr></thead>
        <tbody role="rowgroup">
          <tr v-for="item in patientRiskDistribution" :key="item.id" role="row">
            <th role="rowheader" scope="row">{{ item.name }}</th>
            <td role="cell"><ServiceStatus :tone="item.assessment ? 'done' : 'idle'">{{ item.assessment ? '已有评估' : '暂无评估' }}</ServiceStatus></td>
            <td role="cell"><span class="dashboard-mobile-label" aria-hidden="true">评估类型</span>{{ item.assessment ? assessmentTypeLabel(item.assessment) : '—' }}</td>
            <td role="cell" class="dashboard-score"><span class="dashboard-mobile-label" aria-hidden="true">总分</span>{{ item.assessment?.score ?? '—' }}</td>
            <td role="cell"><span class="dashboard-mobile-label" aria-hidden="true">风险摘要</span>{{ item.summary || (item.assessment ? '暂无风险摘要' : '—') }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <div class="dashboard-insights">
      <section aria-labelledby="dashboard-trend-title">
        <header class="dashboard-section-head"><div><h2 id="dashboard-trend-title">近 7 日情绪趋势</h2><p>日均情绪评分 · 满分 5 分</p></div></header>
        <p v-if="loading" class="dashboard-empty">正在计算趋势…</p>
        <p v-else-if="emotionTrend.every(item => item.value === null)" class="dashboard-empty">近 7 日暂无情绪日记。</p>
        <div v-else class="dashboard-trend" role="img" :aria-label="`近 7 日平均情绪评分（满分 5 分）：${emotionTrend.map(item => `${item.label} ${item.value === null ? '暂无日记' : `${item.value} 分`}`).join('；')}`">
          <div v-for="item in emotionTrend" :key="item.key">
            <div class="dashboard-trend-track"><div :style="{ height: item.percent }" /></div>
            <strong>{{ item.value?.toFixed(1) ?? '—' }}</strong><small>{{ item.label }}</small>
          </div>
        </div>
      </section>
      <section aria-labelledby="dashboard-distribution-title">
        <header class="dashboard-section-head"><div><h2 id="dashboard-distribution-title">评估类型分布</h2><p>最近最多 1000 条可见评估 · 每条只归入一种类型</p></div></header>
        <p v-if="loading" class="dashboard-empty">正在汇总评估…</p>
        <p v-else-if="!assessmentDistribution.length" class="dashboard-empty">当前没有评估数据。</p>
        <ul v-else class="dashboard-distribution">
          <li v-for="item in assessmentDistribution" :key="item.label">
            <div><strong>{{ item.label }}</strong><span>{{ item.value }} 条</span></div>
            <ProgressBar :label="`${item.label}占比，${item.value} 条，共 ${assessments.length} 条`" :value="(item.value / assessments.length) * 100" />
          </li>
        </ul>
      </section>
    </div>
    <section v-if="!loading" class="dashboard-notes" aria-labelledby="dashboard-notes-title">
      <h2 id="dashboard-notes-title">今日重点</h2>
      <p v-if="riskSummary.high">优先跟进 {{ riskSummary.high }} 条高风险预警。</p>
      <p v-if="todayAssessments">今日新增 {{ todayAssessments }} 条评估，可结合干预执行情况安排复评。</p>
      <p v-if="!riskSummary.high && !todayAssessments">暂无高风险预警或新增评估。</p>
    </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard { display: grid; gap: 24px; }
.dashboard-title { padding-bottom: 15px; border-bottom: 1px solid var(--service-gold); }
.dashboard-title h1 { font-size: 31px; line-height: 1.25; font-weight: 750; }
.dashboard-title p, .dashboard-section-head p { margin-top: 4px; color: var(--service-muted); font-size: 13px; }
.dashboard-operations { display: grid; grid-template-columns: minmax(0, 1fr) minmax(245px, .42fr); gap: 24px; }
.dashboard-queue { min-width: 0; background: var(--service-panel); border: 1px solid var(--service-border); border-top: 2px solid var(--service-deep); }
.dashboard-section-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 4px 14px; padding-block: 0 12px; }
.dashboard-section-head h2, .dashboard-metrics h2 { font-size: 19px; font-weight: 720; }
.dashboard-queue .dashboard-section-head { padding: 11px 16px 9px; }
.dashboard-link { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; font-size: 13px; }
.dashboard-link svg { width: 15px; height: 15px; }
.dashboard-risks { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-block: 1px solid var(--service-border); background: var(--workspace-warm); }
.dashboard-risks > div { padding: 9px 16px; min-width: 0; }
.dashboard-risks > div + div { border-left: 1px solid var(--service-border); }
.dashboard-risks dt { color: var(--service-muted); font-size: 12px; }
.dashboard-risks dd { font-variant-numeric: tabular-nums; font-size: 21px; font-weight: 700; overflow-wrap: anywhere; }
.dashboard-risks .risk-high { color: var(--service-red); }
.dashboard-queue-empty, .dashboard-empty { padding: 15px 12px; color: var(--service-muted); font-size: 14px; }
.dashboard-queue-empty { display: flex; align-items: center; gap: 9px; padding: 16px; }
.dashboard-queue-empty svg { width: 17px; height: 17px; color: #3c664f; }
.dashboard-alerts { padding-inline: 16px; }
.dashboard-alerts li { padding-block: 10px; overflow-wrap: anywhere; }
.dashboard-alerts li + li { border-top: 1px solid var(--workspace-line); }
.dashboard-alert-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, .75fr) auto; align-items: center; gap: 8px; font-size: 14px; }
.dashboard-alerts p { margin-top: 4px; color: var(--service-muted); font-size: 13px; }
.dashboard-metrics h2 { padding-bottom: 8px; }
.dashboard-metrics dl { border-top: 1px solid var(--service-border); }
.dashboard-metric { min-height: 53px; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 6px; padding-block: 6px; border-bottom: 1px solid var(--service-border); font-size: 14px; font-weight: 650; }
.dashboard-metric span, .dashboard-metric small { color: var(--service-muted); font-size: 12px; font-weight: 400; }
.dashboard-metric span { display: block; }
.dashboard-metric dd { color: var(--service-ink); font-size: 24px; font-weight: 720; font-variant-numeric: tabular-nums; }
.dashboard-table { width: 100%; table-layout: fixed; text-align: left; overflow-wrap: anywhere; font-size: 14px; }
.dashboard-table thead { background: var(--workspace-warm); color: var(--service-muted); font-size: 12px; }
.dashboard-table :is(th, td) { padding: 12px 10px; border-bottom: 1px solid var(--service-border); }
.dashboard-table th { font-weight: 650; }
.dashboard-table thead th:nth-child(1) { width: 19%; }
.dashboard-table thead th:nth-child(2) { width: 14%; }
.dashboard-table thead th:nth-child(3) { width: 19%; }
.dashboard-table thead th:nth-child(4) { width: 10%; }
.dashboard-score { font-variant-numeric: tabular-nums; }
.dashboard-mobile-label { display: none; }
.dashboard-insights { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.dashboard-insights > section { border-top: 1px solid var(--service-border); padding-top: 14px; }
.dashboard-insights .dashboard-empty { background: var(--workspace-warm); }
.dashboard-trend { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; text-align: center; font-size: 13px; font-variant-numeric: tabular-nums; }
.dashboard-trend-track { display: flex; align-items: end; height: 96px; margin-bottom: 5px; background: var(--workspace-warm); }
.dashboard-trend-track div { width: 100%; background: #665448; }
.dashboard-trend small { display: block; color: var(--service-muted); }
.dashboard-distribution li { padding-block: 10px; border-bottom: 1px solid var(--service-border); font-size: 14px; }
.dashboard-distribution li div { display: flex; justify-content: space-between; gap: 6px; margin-bottom: 7px; font-variant-numeric: tabular-nums; }
.dashboard-notes { display: grid; gap: 6px; padding-top: 14px; border-top: 1px solid var(--service-border); font-size: 14px; color: var(--service-muted); }
.dashboard-notes h2 { color: var(--service-ink); font-weight: 720; }
@media (max-width: 700px) {
  .dashboard { gap: 18px; }
  .dashboard-title h1 { font-size: 25px; }
  .dashboard-operations, .dashboard-insights { grid-template-columns: minmax(0, 1fr); gap: 16px; }
  .dashboard-section-head { padding-bottom: 8px; }
  .dashboard-queue .dashboard-section-head { padding: 8px 10px; }
  .dashboard-risks > div { padding-inline: 10px; }
  .dashboard-queue-empty { padding: 13px 10px; }
  .dashboard-metric { min-height: 40px; }
  .dashboard-metric span { display: inline; margin-left: 6px; }
  .dashboard-metric dd { font-size: 20px; }
  .dashboard-table, .dashboard-table tbody { display: block; }
  .dashboard-table thead { position: absolute; clip-path: inset(50%); width: 1px; height: 1px; overflow: hidden; white-space: nowrap; }
  .dashboard-table tbody tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 12px; align-items: baseline; padding: 10px 0; border-top: 1px solid var(--service-border); }
  .dashboard-table tbody tr:last-child { border-bottom: 1px solid var(--service-border); }
  .dashboard-table tbody :is(th, td) { padding: 0; border: none; }
  .dashboard-table td:last-child { grid-column: 1 / -1; }
  .dashboard-mobile-label { display: inline; margin-right: 6px; color: var(--service-muted); font-size: 12px; }
}
</style>
