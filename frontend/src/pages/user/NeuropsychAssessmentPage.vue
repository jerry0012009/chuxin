<script setup lang="ts">
import { Brain, CheckCircle2, Clock, FileText, Loader2, Play, RefreshCw, ShieldAlert, Sparkles, X } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import NeuropsychFeedbackCard from '@/components/neuropsych/NeuropsychFeedbackCard.vue'
import NeuropsychRunner from '@/components/neuropsych/NeuropsychRunner.vue'
import {
  getFreeNeuropsychTests,
  getMyNeuropsychRecords,
  startFreeNeuropsychRecord,
  startNeuropsychRecord,
  submitNeuropsychRecord,
} from '@/db/api'
import type { NeuropsychRecord, NeuropsychTest, NeuropsychWarningLevel } from '@/types'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const activeTab = ref<'pending' | 'free' | 'completed'>('pending')
const records = ref<NeuropsychRecord[]>([])
const freeTests = ref<NeuropsychTest[]>([])
const runningRecord = ref<NeuropsychRecord | null>(null)
const reportRecord = ref<NeuropsychRecord | null>(null)
const handledRouteKey = ref('')

const warningText: Record<NeuropsychWarningLevel, string> = {
  none: '无明显风险',
  low: '轻度提示',
  middle: '中度关注',
  high: '高风险',
}

const warningClass = (level?: NeuropsychWarningLevel | null) => {
  if (level === 'high') return 'bg-rose-500 text-white'
  if (level === 'middle') return 'bg-amber-500 text-white'
  if (level === 'low') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200'
  return 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'
}

const pendingRecords = computed(() => records.value.filter((item) => item.status !== 'completed' && item.status !== 'expired' && item.status !== 'cancelled'))
const completedRecords = computed(() => records.value.filter((item) => item.status === 'completed'))
const attentionCount = computed(() => records.value.filter((item) => item.warning_level === 'high' || item.warning_level === 'middle').length)

const loadAll = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextRecords, nextFreeTests] = await Promise.all([getMyNeuropsychRecords(), getFreeNeuropsychTests()])
    records.value = nextRecords
    freeTests.value = nextFreeTests
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载神经心理测评失败'
  } finally {
    loading.value = false
  }
}

const handleRouteIntent = async () => {
  const routeKey = route.fullPath
  if (handledRouteKey.value === routeKey) return
  handledRouteKey.value = routeKey

  const recordId = typeof route.params.recordId === 'string' ? route.params.recordId : ''
  const testCode = typeof route.params.testCode === 'string' ? route.params.testCode : ''

  if (route.path.includes('/report/') && recordId) {
    const record = records.value.find((item) => item.id === recordId)
    if (record) {
      reportRecord.value = record
      activeTab.value = 'completed'
    } else {
      errorMessage.value = '未找到该测评报告'
    }
    return
  }

  if (route.path.includes('/records/') && recordId) {
    const record = records.value.find((item) => item.id === recordId)
    if (record) {
      await beginRecord(record)
    } else {
      errorMessage.value = '未找到该待完成测评'
    }
    return
  }

  if (route.path.includes('/free/') && testCode) {
    const test = freeTests.value.find((item) => item.code === testCode)
    if (test) {
      activeTab.value = 'free'
      await beginFree(test)
    } else {
      errorMessage.value = '该自由测评不可用或已停用'
    }
  }
}

const statusText = (record: NeuropsychRecord) => {
  if (record.status === 'completed') return record.calc_status === 'done' ? '已完成' : record.calc_status === 'error' ? '计算失败' : '计算中'
  if (record.status === 'in_progress') return '进行中'
  if (record.status === 'expired') return '已过期'
  if (record.status === 'cancelled') return '已取消'
  return '待完成'
}

const dateText = (value?: string | null) => (value ? new Date(value).toLocaleString('zh-CN') : '未设置')

const beginRecord = async (record: NeuropsychRecord) => {
  errorMessage.value = ''
  try {
    runningRecord.value = await startNeuropsychRecord(record.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '开始测评失败'
  }
}

const beginFree = async (test: NeuropsychTest) => {
  errorMessage.value = ''
  try {
    runningRecord.value = await startFreeNeuropsychRecord(test.code)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '开始自由测评失败'
  }
}

const handleFinished = async (payload: { rawJson: string; rawCsv?: string; testCode?: string }) => {
  if (!runningRecord.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    const completed = await submitNeuropsychRecord(runningRecord.value.id, payload)
    runningRecord.value = null
    reportRecord.value = completed
    await loadAll()
    if (typeof route.query.returnTo === 'string') {
      await router.push(route.query.returnTo)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存测评结果失败'
  } finally {
    submitting.value = false
  }
}

const openReport = (record: NeuropsychRecord) => {
  reportRecord.value = record
}

onMounted(async () => {
  await loadAll()
  await handleRouteIntent()
})
</script>

<template>
  <div class="page-grid py-6 md:py-8">
    <div class="space-y-6">
      <div class="service-card service-band p-4 sm:p-5">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold">
              <Brain class="h-4 w-4" />
              神经心理测评
            </div>
            <h1 class="mt-4 text-3xl font-black md:text-4xl">认知任务与行为测评</h1>
            <p class="mt-3 max-w-2xl text-sm leading-7 text-white/70">
              完成管理员分发的认知实验，或选择已开放的自由测评。结果会生成反馈卡片，帮助你了解当前注意、抑制、风险决策和自我控制表现。
            </p>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div class="rounded-2xl bg-white/10 p-4 text-center">
              <p class="text-2xl font-black">{{ pendingRecords.length }}</p>
              <p class="mt-1 text-xs text-white/60">待完成</p>
            </div>
            <div class="rounded-2xl bg-white/10 p-4 text-center">
              <p class="text-2xl font-black">{{ completedRecords.length }}</p>
              <p class="mt-1 text-xs text-white/60">已完成</p>
            </div>
            <div class="rounded-2xl bg-white/10 p-4 text-center">
              <p class="text-2xl font-black">{{ attentionCount }}</p>
              <p class="mt-1 text-xs text-white/60">需关注</p>
            </div>
          </div>
        </div>
      </div>

      <BaseCard>
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <SectionTitle title="神经心理任务" description="待完成任务来自管理员发布测评任务，自由测评来自管理员开放的测试库。" />
          <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900" type="button" @click="loadAll">
            <RefreshCw class="h-4 w-4" />
            刷新
          </button>
        </div>

        <div class="mt-5 flex gap-2 overflow-x-auto">
          <button
            v-for="tab in [
              { key: 'pending', label: '待完成测评', count: pendingRecords.length },
              { key: 'free', label: '自由测评', count: freeTests.length },
              { key: 'completed', label: '已完成', count: completedRecords.length },
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
          正在加载神经心理测评...
        </div>

        <div v-else-if="activeTab === 'pending'" class="mt-6 grid gap-4">
          <div v-if="pendingRecords.length === 0" class="rounded-3xl bg-slate-50 py-12 text-center dark:bg-slate-900">
            <CheckCircle2 class="mx-auto h-10 w-10 text-slate-300" />
            <p class="mt-3 text-sm font-medium text-slate-500">暂无待完成神经心理测评</p>
          </div>
          <div v-for="record in pendingRecords" :key="record.id" class="rounded-[24px] border border-slate-100 bg-slate-50 p-5 transition hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">{{ statusText(record) }}</span>
                  <span v-if="record.batch_title" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600 dark:bg-blue-950/30 dark:text-blue-200">{{ record.batch_title }}</span>
                </div>
                <h3 class="mt-3 text-lg font-bold text-slate-900 dark:text-white">{{ record.test_title }}</h3>
                <p class="mt-1 max-w-2xl text-sm text-slate-500">{{ record.dimension || record.test_description }}</p>
                <p class="mt-3 text-xs text-slate-400">预计 {{ record.estimated_minutes || '--' }} 分钟</p>
              </div>
              <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-600" type="button" @click="beginRecord(record)">
                <Play class="h-4 w-4" />
                {{ record.status === 'in_progress' ? '继续测评' : '开始测评' }}
              </button>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'free'" class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="test in freeTests" :key="test.id" class="flex flex-col rounded-[24px] border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div class="flex items-start justify-between gap-3">
              <Brain class="h-8 w-8 text-primary" />
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                {{ test.estimated_minutes || '--' }} 分钟
              </span>
            </div>
            <h3 class="mt-4 text-lg font-black text-slate-900 dark:text-white">{{ test.title }}</h3>
            <p class="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">{{ test.description }}</p>
            <p class="mt-3 text-xs font-semibold text-slate-400">{{ test.dimension }}</p>
            <button class="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900" type="button" @click="beginFree(test)">
              <Sparkles class="h-4 w-4" />
              开始自由测评
            </button>
          </div>
        </div>

        <div v-else class="mt-6 grid gap-4">
          <div v-if="completedRecords.length === 0" class="rounded-3xl bg-slate-50 py-12 text-center dark:bg-slate-900">
            <FileText class="mx-auto h-10 w-10 text-slate-300" />
            <p class="mt-3 text-sm font-medium text-slate-500">暂无已完成报告</p>
          </div>
          <div v-for="record in completedRecords" :key="record.id" class="rounded-[24px] border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(record.warning_level)]">{{ warningText[record.warning_level] }}</span>
                <h3 class="mt-3 text-lg font-bold text-slate-900 dark:text-white">{{ record.test_title }}</h3>
                <p class="mt-1 text-sm text-slate-500">{{ record.report?.summary || '报告已生成' }}</p>
                <p class="mt-2 text-xs text-slate-400">完成时间：{{ dateText(record.completed_at) }}</p>
              </div>
              <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900" type="button" @click="openReport(record)">
                <FileText class="h-4 w-4" />
                查看反馈
              </button>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <NeuropsychRunner v-if="runningRecord" :record="runningRecord" :submitting="submitting" @close="runningRecord = null" @finished="handleFinished" />

    <div v-if="reportRecord" class="fixed inset-0 z-[90] overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm">
      <div class="mx-auto my-6 max-w-4xl overflow-hidden rounded-[28px] bg-slate-50 shadow-2xl dark:bg-slate-950">
        <div class="bg-slate-950 p-6 text-white">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs text-white/50">Neuropsych Feedback</p>
              <h2 class="mt-1 text-2xl font-black">{{ reportRecord.test_title || reportRecord.report?.testTitle }}</h2>
              <p class="mt-2 text-sm text-white/70">完成时间：{{ dateText(reportRecord.completed_at || reportRecord.report?.completedAt) }}</p>
            </div>
            <button class="grid h-10 w-10 place-items-center rounded-full bg-white/10 hover:bg-white/20" type="button" @click="reportRecord = null">
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>
        <div class="space-y-5 p-5 md:p-7">
          <div class="rounded-[24px] bg-white p-5 dark:bg-slate-900">
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p class="text-sm text-slate-500">总体反馈</p>
                <h3 class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ reportRecord.report?.summary || '报告已生成' }}</h3>
              </div>
              <span :class="['inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold', warningClass(reportRecord.warning_level)]">
                <ShieldAlert class="h-4 w-4" />
                {{ warningText[reportRecord.warning_level] }}
              </span>
            </div>
            <p v-if="reportRecord.report?.quality?.message" class="mt-4 rounded-2xl bg-slate-50 p-3 text-sm text-slate-500 dark:bg-slate-950">
              {{ reportRecord.report.quality.message }}
            </p>
          </div>

          <NeuropsychFeedbackCard v-for="card in reportRecord.report?.feedbackCards || []" :key="card.title" :card="card" />

          <div v-if="reportRecord.report?.feedback && Object.keys(reportRecord.report.feedback).length" class="rounded-3xl bg-white p-5 dark:bg-slate-900">
            <h3 class="text-sm font-bold text-slate-500">受试者反馈</h3>
            <div v-for="(val, key) in reportRecord.report.feedback" :key="key" class="mt-3">
              <p class="text-xs text-slate-400">{{ key === 'Q0' ? '任务理解' : key === 'Q1' ? '主观评价' : key === 'feedbackRt' ? '反馈耗时' : key }}</p>
              <p class="mt-0.5 text-sm text-slate-700 dark:text-slate-300">{{ key === 'feedbackRt' ? (val / 1000).toFixed(1) + ' 秒' : val }}</p>
            </div>
          </div>

          <div v-if="!(reportRecord.report?.feedbackCards || []).length" class="rounded-3xl bg-white py-12 text-center text-sm text-slate-500 dark:bg-slate-900">
            <Clock class="mx-auto mb-2 h-8 w-8 text-slate-300" />
            报告仍在生成或暂无反馈卡片。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
