<script setup lang="ts">
import { Brain, CheckCircle2, Eye, Loader2, RefreshCw, RotateCcw, Send, ToggleLeft, ToggleRight } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import NeuropsychFeedbackCard from '@/components/neuropsych/NeuropsychFeedbackCard.vue'
import {
  createNeuropsychDistributionPlan,
  getAllProfiles,
  getNeuropsychResultDetail,
  getNeuropsychResults,
  getNeuropsychTests,
  recalculateNeuropsychResult,
  updateNeuropsychTest,
} from '@/db/api'
import type { NeuropsychRecord, NeuropsychTest, NeuropsychWarningLevel, Profile } from '@/types'

const activeTab = ref<'tests' | 'distribute' | 'results'>('tests')
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const tests = ref<NeuropsychTest[]>([])
const results = ref<NeuropsychRecord[]>([])
const profiles = ref<Profile[]>([])
const selectedResult = ref<NeuropsychRecord | null>(null)
const form = ref({
  title: '',
  test_ids: [] as string[],
  user_ids: [] as string[],
})

const patients = computed(() => profiles.value.filter((item) => item.role === 'user'))

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

const loadAll = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextTests, nextResults, nextProfiles] = await Promise.all([
      getNeuropsychTests(),
      getNeuropsychResults(),
      getAllProfiles(),
    ])
    tests.value = nextTests
    results.value = nextResults
    profiles.value = nextProfiles
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载神经心理测评管理端失败'
  } finally {
    loading.value = false
  }
}

const toggleTestStatus = async (test: NeuropsychTest) => {
  saving.value = true
  try {
    await updateNeuropsychTest(test.id, { ...test, status: test.status === 'active' ? 'stopped' : 'active' })
    statusMessage.value = '测试状态已更新'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新测试状态失败'
  } finally {
    saving.value = false
  }
}

const toggleSelfTest = async (test: NeuropsychTest) => {
  saving.value = true
  try {
    await updateNeuropsychTest(test.id, { ...test, self_test_enabled: !test.self_test_enabled })
    statusMessage.value = '自由测评配置已更新'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新自由测评配置失败'
  } finally {
    saving.value = false
  }
}

const submitDistribution = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    await createNeuropsychDistributionPlan(form.value)
    statusMessage.value = '神经心理测评已分发'
    form.value = { title: '', test_ids: [], user_ids: [] }
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '分发失败'
  } finally {
    saving.value = false
  }
}

const openResult = async (record: NeuropsychRecord) => {
  selectedResult.value = await getNeuropsychResultDetail(record.id)
}

const recalc = async (record: NeuropsychRecord) => {
  saving.value = true
  try {
    selectedResult.value = await recalculateNeuropsychResult(record.id)
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重算失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <SectionTitle title="神经心理测评管理端" description="管理测试库、分发认知实验，并查询 Go-NoGo、哥伦比亚卡片和延迟折扣等结果。" />
      <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="loadAll">
        <RefreshCw class="h-4 w-4" />
        刷新
      </button>
    </div>

    <div class="flex gap-2 overflow-x-auto">
      <button
        v-for="tab in [
          { key: 'tests', label: '测试库' },
          { key: 'distribute', label: '分发记录' },
          { key: 'results', label: '结果中心' },
        ]"
        :key="tab.key"
        class="rounded-full px-4 py-2 text-sm font-semibold transition"
        :class="activeTab === tab.key ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'"
        type="button"
        @click="activeTab = tab.key as any"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-medium text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>
    <div v-if="statusMessage" class="rounded-2xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">{{ statusMessage }}</div>

    <BaseCard v-if="loading">
      <div class="flex items-center justify-center gap-2 py-16 text-slate-500"><Loader2 class="h-5 w-5 animate-spin" /> 正在加载...</div>
    </BaseCard>

    <div v-else-if="activeTab === 'tests'" class="grid gap-4 lg:grid-cols-3">
      <BaseCard v-for="test in tests" :key="test.id">
        <div class="flex items-start justify-between gap-4">
          <Brain class="h-9 w-9 text-primary" />
          <span :class="['rounded-full px-3 py-1 text-xs font-bold', test.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500']">
            {{ test.status === 'active' ? '已启用' : '已停用' }}
          </span>
        </div>
        <h3 class="mt-5 text-lg font-black text-slate-900 dark:text-white">{{ test.title }}</h3>
        <p class="mt-2 min-h-18 text-sm leading-6 text-slate-500">{{ test.description }}</p>
        <p class="mt-3 text-xs font-semibold text-slate-400">{{ test.dimension }} / {{ test.estimated_minutes || '--' }} 分钟</p>
        <div class="mt-5 grid gap-2">
          <button class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-700 dark:border-slate-800 dark:text-slate-200" type="button" @click="toggleTestStatus(test)">
            <component :is="test.status === 'active' ? ToggleRight : ToggleLeft" class="h-4 w-4" />
            {{ test.status === 'active' ? '停用测试' : '启用测试' }}
          </button>
          <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="toggleSelfTest(test)">
            <CheckCircle2 class="h-4 w-4" />
            {{ test.self_test_enabled ? '关闭自由测评' : '允许自由测评' }}
          </button>
        </div>
      </BaseCard>
    </div>

    <div v-else-if="activeTab === 'distribute'" class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <BaseCard>
        <SectionTitle title="分发神经心理测评" description="单独分发神经心理任务；组合发布请使用“发布测评任务”。" />
        <div class="mt-5 space-y-4">
          <input v-model="form.title" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950" placeholder="分发主题" />
          <div>
            <p class="mb-2 text-sm font-bold text-slate-700 dark:text-slate-200">选择测试</p>
            <label v-for="test in tests.filter((item) => item.status === 'active')" :key="test.id" class="mb-2 flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-900">
              <input v-model="form.test_ids" :value="test.id" type="checkbox" />
              <span>{{ test.title }}</span>
            </label>
          </div>
          <div>
            <p class="mb-2 text-sm font-bold text-slate-700 dark:text-slate-200">选择患者</p>
            <div class="max-h-60 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
              <label v-for="patient in patients" :key="patient.id" class="mb-1 flex items-center gap-2 rounded-lg p-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-900">
                <input v-model="form.user_ids" :value="patient.id" type="checkbox" />
                <span>{{ patient.full_name || patient.username }}</span>
              </label>
            </div>
          </div>
          <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white disabled:opacity-60" :disabled="saving" type="button" @click="submitDistribution">
            <Send class="h-4 w-4" />
            分发测评
          </button>
        </div>
      </BaseCard>
      <BaseCard>
        <SectionTitle title="最近分发与结果" description="完成后的记录会进入结果中心，可查看原始数据与报告。" />
        <div class="mt-5 space-y-3">
          <div v-for="record in results.slice(0, 8)" :key="record.id" class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-bold text-slate-900 dark:text-white">{{ record.test_title }}</p>
                <p class="text-xs text-slate-500">{{ record.patient_name || record.patient_username }} / {{ record.status }}</p>
              </div>
              <span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(record.warning_level)]">{{ warningText[record.warning_level] }}</span>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <BaseCard v-else>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[900px] text-left text-sm">
          <thead class="text-xs uppercase text-slate-400">
            <tr>
              <th class="px-3 py-3">患者</th>
              <th class="px-3 py-3">测试</th>
              <th class="px-3 py-3">来源</th>
              <th class="px-3 py-3">状态</th>
              <th class="px-3 py-3">预警</th>
              <th class="px-3 py-3">完成时间</th>
              <th class="px-3 py-3">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in results" :key="record.id" class="border-t border-slate-100 dark:border-slate-800">
              <td class="px-3 py-4 font-semibold">{{ record.patient_name || record.patient_username }}</td>
              <td class="px-3 py-4">{{ record.test_title }}</td>
              <td class="px-3 py-4">{{ record.source_type === 'self' ? '自由测评' : record.batch_title || '管理员分发' }}</td>
              <td class="px-3 py-4">{{ record.status }} / {{ record.calc_status }}</td>
              <td class="px-3 py-4"><span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(record.warning_level)]">{{ warningText[record.warning_level] }}</span></td>
              <td class="px-3 py-4">{{ record.completed_at ? new Date(record.completed_at).toLocaleString('zh-CN') : '--' }}</td>
              <td class="px-3 py-4">
                <div class="flex gap-2">
                  <button class="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 dark:bg-slate-800" type="button" @click="openResult(record)"><Eye class="h-4 w-4" /></button>
                  <button class="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 dark:bg-slate-800" type="button" @click="recalc(record)"><RotateCcw class="h-4 w-4" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>

    <div v-if="selectedResult" class="fixed inset-0 z-[90] overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm">
      <div class="mx-auto my-6 max-w-5xl overflow-hidden rounded-[28px] bg-slate-50 shadow-2xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-4 bg-slate-950 p-6 text-white">
          <div>
            <p class="text-xs text-white/50">Neuropsych Result</p>
            <h2 class="mt-1 text-2xl font-black">{{ selectedResult.test_title }}</h2>
            <p class="mt-2 text-sm text-white/60">{{ selectedResult.patient_name || selectedResult.patient_username }}</p>
          </div>
          <button class="rounded-full bg-white/10 px-3 py-2 text-sm" type="button" @click="selectedResult = null">关闭</button>
        </div>
        <div class="grid gap-5 p-5 lg:grid-cols-[1fr_1fr]">
          <NeuropsychFeedbackCard v-for="card in selectedResult.report?.feedbackCards || []" :key="card.title" :card="card" />
          <div class="rounded-[24px] bg-white p-5 dark:bg-slate-900">
            <h3 class="font-bold text-slate-900 dark:text-white">核心指标</h3>
            <pre class="mt-4 max-h-96 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{{ JSON.stringify(selectedResult.metrics_json || selectedResult.report?.metrics || {}, null, 2) }}</pre>
          </div>
          <div class="rounded-[24px] bg-white p-5 dark:bg-slate-900 lg:col-span-2">
            <h3 class="font-bold text-slate-900 dark:text-white">原始数据预览</h3>
            <pre class="mt-4 max-h-96 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{{ JSON.stringify(selectedResult.report?.rawDataPreview || [], null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
