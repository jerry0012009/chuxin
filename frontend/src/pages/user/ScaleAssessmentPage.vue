<script setup lang="ts">
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  FileText,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { getFreeScaleSurveys, getMyScaleRecords, startFreeScaleRecord, startScaleRecord, submitScaleRecord } from '@/db/api'
import type { ScaleDistributionRecord, ScaleQuestion, ScaleSurvey, ScaleWarningLevel } from '@/types'

const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const activeTab = ref<'pending' | 'free' | 'completed' | 'all'>('pending')
const records = ref<ScaleDistributionRecord[]>([])
const freeSurveys = ref<ScaleSurvey[]>([])
const answeringRecord = ref<ScaleDistributionRecord | null>(null)
const reportRecord = ref<ScaleDistributionRecord | null>(null)
const reportReturnTo = ref('')
const reportCountdown = ref(0)
const currentQuestionIndex = ref(0)
const answerDraft = ref<Record<string, string | string[]>>({})
const route = useRoute()
const router = useRouter()
let reportReturnTimer: ReturnType<typeof setTimeout> | null = null
let reportCountdownTimer: ReturnType<typeof setInterval> | null = null

const warningText: Record<ScaleWarningLevel, string> = {
  none: '无明显风险',
  low: '低风险',
  middle: '中风险',
  high: '高风险',
}

const warningClass = (level?: ScaleWarningLevel | null) => {
  if (level === 'high') return 'bg-rose-500 text-white'
  if (level === 'middle') return 'bg-amber-500 text-white'
  if (level === 'low') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200'
  return 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'
}
const warningLabel = (level?: ScaleWarningLevel | null) => warningText[level || 'none'] || '未计算'

const pendingRecords = computed(() =>
  records.value.filter((item) => item.status !== 'completed' && item.status !== 'expired' && item.status !== 'cancelled'),
)
const completedRecords = computed(() => records.value.filter((item) => item.status === 'completed'))
const highRiskCount = computed(() => records.value.filter((item) => item.warning_level === 'high' || item.warning_level === 'middle').length)

const filteredRecords = computed(() => {
  if (activeTab.value === 'pending') return pendingRecords.value
  if (activeTab.value === 'free') return []
  if (activeTab.value === 'completed') return completedRecords.value
  return records.value
})

const activeSurvey = computed(() => answeringRecord.value?.survey || answeringRecord.value?.report?.survey || null)
const shouldAutoAdvanceQuestion = (question?: ScaleQuestion | null) =>
  Boolean(question && question.question_type !== 'checkbox' && question.question_type !== 'text')
const questions = computed<ScaleQuestion[]>(() => {
  const raw = ((activeSurvey.value as any)?.questions || []) as ScaleQuestion[]
  return raw.slice().sort((a: ScaleQuestion, b: ScaleQuestion) => (a.order_no || 0) - (b.order_no || 0))
})
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value] || null)
const progress = computed(() => (questions.value.length ? ((currentQuestionIndex.value + 1) / questions.value.length) * 100 : 0))
const currentQuestionAutoAdvances = computed(() => shouldAutoAdvanceQuestion(currentQuestion.value))

const loadRecords = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextRecords, nextFreeSurveys] = await Promise.all([getMyScaleRecords(), getFreeScaleSurveys()])
    records.value = nextRecords
    freeSurveys.value = nextFreeSurveys
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载量表测评失败'
  } finally {
    loading.value = false
  }
}

const clearReportReturnTimers = () => {
  if (reportReturnTimer) {
    clearTimeout(reportReturnTimer)
    reportReturnTimer = null
  }
  if (reportCountdownTimer) {
    clearInterval(reportCountdownTimer)
    reportCountdownTimer = null
  }
}

const closeReport = async () => {
  clearReportReturnTimers()
  const returnTo = reportReturnTo.value
  reportRecord.value = null
  reportReturnTo.value = ''
  reportCountdown.value = 0
  if (returnTo) {
    await router.push(returnTo)
  }
}

const scheduleTaskReportReturn = (returnTo: string) => {
  clearReportReturnTimers()
  reportReturnTo.value = returnTo
  reportCountdown.value = 15
  reportCountdownTimer = setInterval(() => {
    reportCountdown.value = Math.max(0, reportCountdown.value - 1)
  }, 1000)
  reportReturnTimer = setTimeout(() => {
    void closeReport()
  }, 15000)
}

const handleRouteIntent = async () => {
  if (route.query.tab === 'completed') activeTab.value = 'completed'
  const recordId = typeof route.query.recordId === 'string' ? route.query.recordId : ''
  if (!recordId) return
  const record = records.value.find((item) => item.id === recordId)
  if (record && record.status !== 'completed') {
    await startAnswer(record)
  } else if (record) {
    openReport(record)
  } else {
    errorMessage.value = '未找到该量表任务'
  }
}

const statusText = (record: ScaleDistributionRecord) => {
  if (record.status === 'completed') return record.calc_status === 'done' ? '已完成' : record.calc_status === 'error' ? '计算失败' : '计算中'
  if (record.status === 'in_progress') return '进行中'
  if (record.status === 'expired') return '已过期'
  if (record.status === 'cancelled') return '已取消'
  return '待完成'
}

const dateText = (value?: string | null) => (value ? new Date(value).toLocaleString('zh-CN') : '未设置')

const startAnswer = async (record: ScaleDistributionRecord) => {
  errorMessage.value = ''
  try {
    const next = await startScaleRecord(record.id)
    answeringRecord.value = next
    currentQuestionIndex.value = 0
    answerDraft.value = {}
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '开始测评失败'
  }
}

const startFreeAnswer = async (survey: ScaleSurvey) => {
  errorMessage.value = ''
  try {
    const next = await startFreeScaleRecord(survey.code || survey.id)
    answeringRecord.value = next
    currentQuestionIndex.value = 0
    answerDraft.value = {}
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '开始自由测评失败'
  }
}

const answerValue = (question: ScaleQuestion) => answerDraft.value[question.id]

const setSingleAnswer = (question: ScaleQuestion, optionId: string) => {
  answerDraft.value = { ...answerDraft.value, [question.id]: optionId }
  if (shouldAutoAdvanceQuestion(question)) {
    window.setTimeout(() => {
      if (answerDraft.value[question.id] !== optionId || currentQuestion.value?.id !== question.id) return
      advanceAfterAutoAnswer()
    }, 180)
  }
}

const setTextAnswer = (question: ScaleQuestion, value: string) => {
  answerDraft.value = { ...answerDraft.value, [question.id]: value }
}

const toggleMultiAnswer = (question: ScaleQuestion, optionId: string) => {
  const current = Array.isArray(answerDraft.value[question.id]) ? [...(answerDraft.value[question.id] as string[])] : []
  const next = current.includes(optionId) ? current.filter((item) => item !== optionId) : [...current, optionId]
  answerDraft.value = { ...answerDraft.value, [question.id]: next }
}

const questionAnswered = (question: ScaleQuestion) => {
  const value = answerDraft.value[question.id]
  return Array.isArray(value) ? value.length > 0 : Boolean(String(value || '').trim())
}

const goNext = () => {
  if (!currentQuestion.value) return
  if (currentQuestion.value.required && !questionAnswered(currentQuestion.value)) {
    errorMessage.value = '请先完成当前题目'
    return
  }
  errorMessage.value = ''
  currentQuestionIndex.value = Math.min(currentQuestionIndex.value + 1, questions.value.length - 1)
}

const goPrev = () => {
  errorMessage.value = ''
  currentQuestionIndex.value = Math.max(0, currentQuestionIndex.value - 1)
}

const advanceAfterAutoAnswer = () => {
  errorMessage.value = ''
  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value += 1
    return
  }
  void submitAnswers()
}

const submitAnswers = async () => {
  if (!answeringRecord.value) return
  const firstMissing = questions.value.find((question) => question.required && !questionAnswered(question))
  if (firstMissing) {
    currentQuestionIndex.value = questions.value.findIndex((item) => item.id === firstMissing.id)
    errorMessage.value = '还有必答题未完成'
    return
  }
  submitting.value = true
  errorMessage.value = ''
  try {
    const answers = questions.value.map((question) => {
      const value = answerDraft.value[question.id]
      return {
        questionId: question.id,
        questionType: question.question_type,
        myAnswer: Array.isArray(value) ? value.join(',') : String(value || ''),
      }
    })
    const completed = await submitScaleRecord(answeringRecord.value.id, answers)
    answeringRecord.value = null
    reportRecord.value = completed
    await loadRecords()
    if (typeof route.query.returnTo === 'string') {
      scheduleTaskReportReturn(route.query.returnTo)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提交测评失败'
  } finally {
    submitting.value = false
  }
}

const openReport = (record: ScaleDistributionRecord) => {
  clearReportReturnTimers()
  reportReturnTo.value = ''
  reportCountdown.value = 0
  reportRecord.value = record
}

onMounted(async () => {
  await loadRecords()
  await handleRouteIntent()
})

onBeforeUnmount(clearReportReturnTimers)
</script>

<template>
  <div class="page-grid py-6 md:py-8">
    <div class="space-y-6">
      <div class="service-card service-card-highlight p-4 sm:p-5">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div class="inline-flex items-center gap-2 text-xs font-semibold text-primary">
              <ClipboardList class="h-4 w-4" />
              独立量表测评
            </div>
            <h1 class="mt-2 text-xl font-bold md:text-2xl">量表测评</h1>
            <p class="service-muted mt-2 max-w-2xl text-sm leading-6">
              查看管理员分发的标准化量表任务，也可以进入管理员开放的自由测评，完成后自动生成维度报告和风险提示。
            </p>
          </div>
          <div class="service-stats grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div class="p-3 text-center">
              <p class="text-2xl font-black">{{ pendingRecords.length }}</p>
              <p class="service-muted mt-1 text-xs">待完成</p>
            </div>
            <div class="p-3 text-center">
              <p class="text-2xl font-black">{{ freeSurveys.length }}</p>
              <p class="service-muted mt-1 text-xs">自由测评</p>
            </div>
            <div class="p-3 text-center">
              <p class="text-2xl font-black">{{ completedRecords.length }}</p>
              <p class="service-muted mt-1 text-xs">已完成</p>
            </div>
            <div class="p-3 text-center">
              <p class="text-2xl font-black">{{ highRiskCount }}</p>
              <p class="service-muted mt-1 text-xs">需关注</p>
            </div>
          </div>
        </div>
      </div>

      <BaseCard>
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <SectionTitle title="我的测评任务" description="AI评估与量表测评相互独立，这里展示管理员分发任务与已开放的自由量表。" />
          <button class="service-button service-outline" type="button" @click="loadRecords">
            <RefreshCw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div class="mt-5 flex gap-2 overflow-x-auto">
          <button
            v-for="tab in [
              { key: 'pending', label: '待完成', count: pendingRecords.length },
              { key: 'free', label: '自由测评', count: freeSurveys.length },
              { key: 'completed', label: '已完成', count: completedRecords.length },
              { key: 'all', label: '全部', count: records.length },
            ]"
            :key="tab.key"
            class="rounded-full px-4 py-2 text-sm font-semibold transition"
            :class="activeTab === tab.key ? 'bg-primary text-white shadow-lg shadow-blue-500/20' : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'"
            type="button"
            @click="activeTab = tab.key as any"
          >
            {{ tab.label }} {{ tab.count }}
          </button>
        </div>

        <div v-if="errorMessage" class="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-medium text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">
          {{ errorMessage }}
        </div>

        <div v-if="loading" class="mt-8 flex items-center justify-center gap-2 rounded-3xl bg-slate-50 py-12 text-slate-500 dark:bg-slate-900">
          <Loader2 class="h-5 w-5 animate-spin" />
          正在加载量表任务...
        </div>

        <div v-else-if="activeTab === 'free'" class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div
            v-for="survey in freeSurveys"
            :key="survey.id"
            class="flex flex-col rounded-[24px] border border-slate-100 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-blue-900"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <span class="rounded-full bg-white px-3 py-1 text-xs font-bold text-primary dark:bg-slate-800">自由测评</span>
                <h3 class="mt-4 text-lg font-black text-slate-900 dark:text-white">{{ survey.title }}</h3>
                <p class="mt-2 text-sm leading-6 text-slate-500">{{ survey.description || '管理员已开放该量表，可自主完成并查看反馈报告。' }}</p>
              </div>
              <ClipboardList class="h-7 w-7 shrink-0 text-primary" />
            </div>
            <div class="mt-auto pt-5">
              <p class="mb-3 text-xs text-slate-400">{{ survey.survey_type || '量表测评' }} · {{ survey.question_count || survey.questions?.length || 0 }} 题</p>
              <button
                class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-600"
                type="button"
                @click="startFreeAnswer(survey)"
              >
                <ClipboardList class="h-4 w-4" />
                开始自由测评
              </button>
            </div>
          </div>
          <div v-if="freeSurveys.length === 0" class="rounded-3xl bg-slate-50 py-12 text-center dark:bg-slate-900 md:col-span-2 xl:col-span-3">
            <FileText class="mx-auto h-10 w-10 text-slate-300" />
            <p class="mt-3 text-sm font-medium text-slate-500">暂无开放的自由量表</p>
          </div>
        </div>

        <div v-else-if="filteredRecords.length === 0" class="mt-8 rounded-3xl bg-slate-50 py-12 text-center dark:bg-slate-900">
          <FileText class="mx-auto h-10 w-10 text-slate-300" />
          <p class="mt-3 text-sm font-medium text-slate-500">暂无对应状态的量表任务</p>
        </div>

        <div v-else class="mt-6 grid gap-4">
          <div
            v-for="record in filteredRecords"
            :key="record.id"
            class="rounded-[24px] border border-slate-100 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-blue-900"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(record.warning_level)]">
                    {{ warningText[record.warning_level] || '未计算' }}
                  </span>
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                    {{ statusText(record) }}
                  </span>
                </div>
                <h3 class="mt-3 text-lg font-bold text-slate-900 dark:text-white">{{ record.survey_title || '未命名量表' }}</h3>
                <p class="mt-1 text-sm text-slate-500">{{ record.plan_title || '量表测评' }}</p>
                <p class="mt-3 text-xs text-slate-400">有效期：{{ dateText(record.start_at) }} - {{ dateText(record.end_at) }}</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="record.status !== 'completed' && record.status !== 'expired' && record.status !== 'cancelled'"
                  class="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-600"
                  type="button"
                  @click="startAnswer(record)"
                >
                  <ClipboardList class="h-4 w-4" />
                  {{ record.status === 'in_progress' ? '继续测评' : '开始测评' }}
                </button>
                <button
                  v-if="record.status === 'completed'"
                  class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
                  type="button"
                  @click="openReport(record)"
                >
                  <FileText class="h-4 w-4" />
                  查看报告
                </button>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <div v-if="answeringRecord && currentQuestion" class="service-dialog fixed inset-0 z-[70] bg-slate-950/60 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="scale-question-title">
      <div class="service-card mx-auto my-2 max-w-3xl overflow-hidden shadow-xl sm:my-6">
        <div class="service-panel-heading p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-bold text-primary/70">量表答题</p>
              <h2 id="scale-question-title" class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ answeringRecord.survey_title }}</h2>
            </div>
            <button class="grid h-10 w-10 shrink-0 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" type="button" aria-label="关闭答题" @click="answeringRecord = null">
              <X class="h-5 w-5 text-slate-400" />
            </button>
          </div>
          <div class="mt-5 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div class="h-full rounded-full bg-primary transition-all" :style="{ width: `${progress}%` }" />
          </div>
          <p class="mt-2 text-xs text-slate-400">第 {{ currentQuestionIndex + 1 }} / {{ questions.length }} 题</p>
        </div>

        <div class="p-5 md:p-7">
          <h3 class="text-xl font-bold leading-8 text-slate-900 dark:text-white">{{ currentQuestion.stem }}</h3>
          <p class="mt-2 text-sm text-slate-400">{{ currentQuestion.required ? '必答题' : '选答题' }}</p>

          <div v-if="currentQuestion.question_type === 'text'" class="mt-6">
            <textarea
              class="min-h-36 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm outline-none transition focus:border-primary focus:ring-4 focus:ring-blue-500/10 dark:border-slate-800 dark:bg-slate-900"
              :value="String(answerValue(currentQuestion) || '')"
              placeholder="请输入你的答案"
              @input="setTextAnswer(currentQuestion, ($event.target as HTMLTextAreaElement).value)"
            />
          </div>
          <div v-else class="mt-6 grid gap-3">
            <button
              v-for="option in currentQuestion.options || []"
              :key="option.id"
              class="flex w-full items-center justify-between gap-4 rounded-2xl border p-4 text-left transition"
              :class="
                currentQuestion.question_type === 'checkbox'
                  ? (Array.isArray(answerValue(currentQuestion)) && (answerValue(currentQuestion) as string[]).includes(option.id)
                    ? 'border-primary bg-blue-50 text-primary dark:bg-blue-950/30'
                    : 'border-slate-200 bg-white hover:border-blue-200 dark:border-slate-800 dark:bg-slate-900')
                  : answerValue(currentQuestion) === option.id
                    ? 'border-primary bg-blue-50 text-primary dark:bg-blue-950/30'
                    : 'border-slate-200 bg-white hover:border-blue-200 dark:border-slate-800 dark:bg-slate-900'
              "
              type="button"
              @click="currentQuestion.question_type === 'checkbox' ? toggleMultiAnswer(currentQuestion, option.id) : setSingleAnswer(currentQuestion, option.id)"
            >
              <span class="font-semibold">{{ option.option_no }}. {{ option.label }}</span>
              <CheckCircle2
                v-if="currentQuestion.question_type === 'checkbox' ? Array.isArray(answerValue(currentQuestion)) && (answerValue(currentQuestion) as string[]).includes(option.id) : answerValue(currentQuestion) === option.id"
                class="h-5 w-5"
              />
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between gap-3 border-t border-slate-100 p-5 dark:border-slate-800">
          <button class="service-button service-outline" :disabled="currentQuestionIndex === 0" type="button" @click="goPrev">
            <ChevronLeft class="h-4 w-4" />
            上一题
          </button>
          <button
            v-if="!currentQuestionAutoAdvances && currentQuestionIndex < questions.length - 1"
            class="service-button"
            type="button"
            @click="goNext"
          >
            下一题
            <ChevronRight class="h-4 w-4" />
          </button>
          <button
            v-else-if="!currentQuestionAutoAdvances"
            class="service-button"
            :disabled="submitting"
            type="button"
            @click="submitAnswers"
          >
            <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
            提交测评
          </button>
        </div>
      </div>
    </div>

    <div v-if="reportRecord" class="service-dialog fixed inset-0 z-[80] bg-slate-950/60 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="scale-report-title">
      <div class="service-card mx-auto my-2 max-w-4xl overflow-hidden shadow-xl sm:my-6">
        <div class="service-band p-5 sm:p-6">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs text-white/80">量表测评报告</p>
              <h2 id="scale-report-title" class="mt-1 text-2xl font-black">{{ reportRecord.survey_title || reportRecord.report?.surveyTitle }}</h2>
              <p class="mt-2 text-sm text-white/70">完成时间：{{ dateText(reportRecord.completed_at) }}</p>
            </div>
            <button class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white/10 hover:bg-white/20" type="button" aria-label="关闭报告" @click="closeReport">
              <X class="h-5 w-5" />
            </button>
          </div>
          <p v-if="reportReturnTo" class="mt-4 rounded-2xl bg-white/10 px-4 py-2 text-sm font-bold text-white/80">
            报告将展示 {{ reportCountdown }} 秒，关闭后返回任务中心。
          </p>
        </div>
        <div class="grid gap-5 p-5 md:grid-cols-[0.8fr_1.2fr] md:p-7">
          <div class="rounded-3xl bg-slate-50 p-5 dark:bg-slate-900">
            <p class="text-sm text-slate-500">总分</p>
            <p class="mt-2 text-5xl font-black text-slate-900 dark:text-white">{{ reportRecord.total_score ?? reportRecord.report?.totalScore ?? '--' }}</p>
            <span :class="['mt-4 inline-flex rounded-full px-3 py-1 text-xs font-bold', warningClass(reportRecord.warning_level)]">
              {{ warningText[reportRecord.warning_level] || '未计算' }}
            </span>
            <p v-if="reportRecord.calc_status === 'error'" class="mt-4 rounded-2xl bg-rose-50 p-3 text-sm text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">
              {{ reportRecord.calc_error || '计算失败' }}
            </p>
          </div>
          <div class="space-y-4">
            <div
              v-for="dimension in reportRecord.report?.dimensions || reportRecord.dimensions || []"
              :key="dimension.dimensionId || dimension.id"
              class="rounded-3xl border border-slate-100 p-5 dark:border-slate-800"
            >
              <div class="flex items-center justify-between gap-4">
                <h3 class="font-bold text-slate-900 dark:text-white">{{ dimension.name || dimension.dimension_name }}</h3>
                <span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(dimension.warningLevel || dimension.warning_level)]">
              {{ warningLabel(dimension.warningLevel || dimension.warning_level) }}
                </span>
              </div>
              <p class="mt-3 text-sm text-slate-500">原始分 {{ dimension.rawScore ?? dimension.raw_score ?? 0 }} / 标准分 {{ dimension.standardScore ?? dimension.standard_score ?? 0 }}</p>
              <p v-if="dimension.conclusion" class="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-300">{{ dimension.conclusion }}</p>
              <p v-if="dimension.suggestion" class="mt-2 rounded-2xl bg-blue-50 p-3 text-sm leading-7 text-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
                {{ dimension.suggestion }}
              </p>
            </div>
            <div v-if="!(reportRecord.report?.dimensions || reportRecord.dimensions || []).length" class="rounded-3xl bg-slate-50 p-8 text-center text-sm text-slate-500 dark:bg-slate-900">
              <AlertTriangle class="mx-auto mb-2 h-6 w-6 text-slate-300" />
              报告还在生成或暂无维度结果。
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
