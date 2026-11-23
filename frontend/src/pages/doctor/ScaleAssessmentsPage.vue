<script setup lang="ts">
import { assessmentStatusLabel } from '@/lib/assessment-display'
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Copy,
  Download,
  Eye,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Send,
  Upload,
  X,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import {
  cloneScaleSurvey,
  createScaleDistributionPlan,
  createScaleSurvey,
  exportScaleResults,
  getAllProfiles,
  getScaleDistributionPlans,
  getScaleResultDetail,
  getScaleResults,
  getScaleSurveys,
  getScaleSurvey,
  importHuaxinyunScaleSurveys,
  importScaleAnswers,
  publishScaleSurvey,
  recalculateScaleResult,
  reorderScaleSurveys,
  updateScaleSurvey,
} from '@/db/api'
import type { HuaxinyunScaleImportResult, Profile, ScaleDistributionPlan, ScaleDistributionRecord, ScaleSurvey, ScaleWarningLevel } from '@/types'

const activeTab = ref<'surveys' | 'distributions' | 'results'>('surveys')
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const surveys = ref<ScaleSurvey[]>([])
const plans = ref<ScaleDistributionPlan[]>([])
const results = ref<ScaleDistributionRecord[]>([])
const profiles = ref<Profile[]>([])
const editingSurvey = ref<ScaleSurvey | null>(null)
const detailRecord = ref<ScaleDistributionRecord | null>(null)
const detailLoading = ref(false)
const importContent = ref('')
const huaxinyunImportOpen = ref(false)
const huaxinyunImportContent = ref('')
const huaxinyunImportFileName = ref('')
const huaxinyunImportPublish = ref(false)
const huaxinyunImportOverwrite = ref(false)
const huaxinyunImportSkipInvalid = ref(true)
const huaxinyunImportLoading = ref(false)
const huaxinyunImportResult = ref<HuaxinyunScaleImportResult | null>(null)
const form = ref({
  id: '',
  title: '',
  code: '',
  description: '',
  survey_type: '抑郁筛查',
  self_test_enabled: false,
  schema: '',
})
const distributionForm = ref({
  title: '',
  assessment_category: 'scale' as 'scale' | 'neuropsych',
  survey_ids: [] as string[],
  user_ids: [] as string[],
  start_at: '',
  end_at: '',
})

const defaultSchema = () =>
  JSON.stringify(
    {
      questions: Array.from({ length: 9 }, (_, index) => ({
        id: crypto.randomUUID(),
        question_type: 'radio',
        stem: `PHQ-9 第 ${index + 1} 题：请填写正式题干`,
        order_no: index + 1,
        required: true,
        options: [
          { id: crypto.randomUUID(), option_no: 'A', label: '完全没有', value: 0, order_no: 1 },
          { id: crypto.randomUUID(), option_no: 'B', label: '有几天', value: 1, order_no: 2 },
          { id: crypto.randomUUID(), option_no: 'C', label: '一半以上时间', value: 2, order_no: 3 },
          { id: crypto.randomUUID(), option_no: 'D', label: '几乎每天', value: 3, order_no: 4 },
        ],
      })),
      dimensions: [
        {
          id: crypto.randomUUID(),
          name: '抑郁风险总分',
          code: 'PHQ_TOTAL',
          num: 1,
          raw_score_formula: 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9',
          standard_score_formula: '',
          show_in_full_report: true,
          show_in_user_report: true,
          show_chart: true,
          result_definitions: [
            { id: crypto.randomUUID(), condition_expression: 'hx_wd_y_1 <= 4', conclusion: '当前量表结果未提示明显风险。', suggestion: '建议保持规律作息并持续观察。', warning_level: 'none', order_no: 1 },
            { id: crypto.randomUUID(), condition_expression: 'hx_wd_y_1 >= 5 && hx_wd_y_1 <= 9', conclusion: '当前结果提示轻度风险。', suggestion: '建议增加自我照护，并在必要时联系管理员。', warning_level: 'low', order_no: 2 },
            { id: crypto.randomUUID(), condition_expression: 'hx_wd_y_1 >= 10 && hx_wd_y_1 <= 14', conclusion: '当前结果提示中度风险。', suggestion: '建议管理员尽快随访，并结合临床访谈进一步评估。', warning_level: 'middle', order_no: 3 },
            { id: crypto.randomUUID(), condition_expression: 'hx_wd_y_1 >= 15', conclusion: '当前结果提示高风险。', suggestion: '建议立即联系管理员进行专业评估和干预。', warning_level: 'high', order_no: 4 },
          ],
        },
      ],
    },
    null,
    2,
  )

const patients = computed(() => profiles.value.filter((item) => item.role === 'user'))
const publishedSurveys = computed(() => surveys.value.filter((item) => item.status === 'published'))
const toastMessage = computed(() => errorMessage.value || statusMessage.value)

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

const loadAll = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextSurveys, nextPlans, nextResults, nextProfiles] = await Promise.all([
      getScaleSurveys(),
      getScaleDistributionPlans(),
      getScaleResults(),
      getAllProfiles(),
    ])
    surveys.value = nextSurveys
    plans.value = nextPlans
    results.value = nextResults
    profiles.value = nextProfiles
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载量表测评工作台失败'
  } finally {
    loading.value = false
  }
}

const resetSurveyForm = () => {
  editingSurvey.value = null
  form.value = {
    id: '',
    title: '',
    code: `scale-${Date.now()}`,
    description: '',
    survey_type: '抑郁筛查',
    self_test_enabled: false,
    schema: defaultSchema(),
  }
}

const editSurvey = async (survey: ScaleSurvey) => {
  editingSurvey.value = survey
  // Fetch full detail including questions, dimensions, result_definitions
  const full = await getScaleSurvey(survey.id)
  editingSurvey.value = full
  form.value = {
    id: full.id,
    title: full.title,
    code: full.code,
    description: full.description || '',
    survey_type: full.survey_type || '抑郁筛查',
    self_test_enabled: full.self_test_enabled,
    schema: JSON.stringify({ questions: full.questions || [], dimensions: full.dimensions || [] }, null, 2),
  }
}

const saveSurvey = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    const schema = JSON.parse(form.value.schema || '{}')
    const payload = {
      title: form.value.title,
      code: form.value.code,
      description: form.value.description,
      survey_type: form.value.survey_type,
      self_test_enabled: form.value.self_test_enabled,
      questions: schema.questions || [],
      dimensions: schema.dimensions || [],
    }
    if (editingSurvey.value) {
      await updateScaleSurvey(editingSurvey.value.id, payload as any)
      statusMessage.value = '量表已保存'
    } else {
      await createScaleSurvey(payload as any)
      statusMessage.value = '量表已创建'
    }
    resetSurveyForm()
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存量表失败，请检查 JSON 结构'
  } finally {
    saving.value = false
  }
}

const publishSurvey = async (survey: ScaleSurvey) => {
  saving.value = true
  errorMessage.value = ''
  try {
    await publishScaleSurvey(survey.id)
    statusMessage.value = '量表已发布'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布失败'
  } finally {
    saving.value = false
  }
}

const moveSurvey = async (survey: ScaleSurvey, direction: 'up' | 'down') => {
  const idx = surveys.value.findIndex(s => s.id === survey.id)
  if (idx < 0) return
  const targetIdx = direction === 'up' ? idx - 1 : idx + 1
  if (targetIdx < 0 || targetIdx >= surveys.value.length) return
  const target = surveys.value[targetIdx]
  if (!target) return
  // Swap sort_order values
  const surveyOrder = (survey as any).sort_order ?? idx + 1
  const targetOrder = (target as any).sort_order ?? targetIdx + 1
  try {
    await reorderScaleSurveys([
      { id: survey.id, sort_order: targetOrder },
      { id: target!.id, sort_order: surveyOrder },
    ])
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '排序失败'
  }
}

const toggleSelfTest = async (survey: ScaleSurvey) => {
  saving.value = true
  errorMessage.value = ''
  try {
    await updateScaleSurvey(survey.id, {
      title: survey.title,
      code: survey.code,
      description: survey.description,
      survey_type: survey.survey_type,
      self_test_enabled: !survey.self_test_enabled,
    } as any)
    statusMessage.value = survey.self_test_enabled ? '已关闭量表自由测评' : '已开放量表自由测评'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新自由测评配置失败'
  } finally {
    saving.value = false
  }
}

const copySurvey = async (survey: ScaleSurvey) => {
  await cloneScaleSurvey(survey.id)
  statusMessage.value = '已复制量表'
  await loadAll()
}

const openHuaxinyunImport = () => {
  errorMessage.value = ''
  statusMessage.value = ''
  huaxinyunImportOpen.value = true
  huaxinyunImportResult.value = null
}

const handleHuaxinyunFile = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  huaxinyunImportFileName.value = file.name
  huaxinyunImportContent.value = await file.text()
  huaxinyunImportResult.value = null
  input.value = ''
}

const runHuaxinyunImport = async (dryRun: boolean) => {
  if (!huaxinyunImportContent.value.trim()) {
    errorMessage.value = '请先选择或粘贴华心云量表 JSON'
    return
  }
  huaxinyunImportLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    const result = await importHuaxinyunScaleSurveys({
      content: huaxinyunImportContent.value,
      dry_run: dryRun,
      publish: huaxinyunImportPublish.value,
      overwrite: huaxinyunImportOverwrite.value,
      skip_invalid: huaxinyunImportSkipInvalid.value,
    })
    huaxinyunImportResult.value = result
    statusMessage.value = dryRun
      ? `预检完成：${result.importable}/${result.total} 可导入，${result.publishable} 可发布`
      : `导入完成：新增 ${result.imported}，更新 ${result.updated}，跳过 ${result.skipped}，失败 ${result.failed}`
    if (!dryRun) {
      await loadAll()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '华心云量表导入失败'
  } finally {
    huaxinyunImportLoading.value = false
  }
}

const toggleSelected = (collection: string[], value: string) =>
  collection.includes(value) ? collection.filter((item) => item !== value) : [...collection, value]

const createDistribution = async () => {
  saving.value = true
  errorMessage.value = ''
  try {
    await createScaleDistributionPlan({
      title: distributionForm.value.title,
      assessment_category: distributionForm.value.assessment_category,
      survey_ids: distributionForm.value.survey_ids,
      recipient_user_ids: distributionForm.value.user_ids,
      start_at: distributionForm.value.start_at ? new Date(distributionForm.value.start_at).toISOString() : undefined,
      end_at: distributionForm.value.end_at ? new Date(distributionForm.value.end_at).toISOString() : undefined,
    })
    statusMessage.value = '分发计划已创建'
    distributionForm.value = { title: '', assessment_category: 'scale', survey_ids: [], user_ids: [], start_at: '', end_at: '' }
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建分发失败'
  } finally {
    saving.value = false
  }
}

const openResult = async (record: ScaleDistributionRecord) => {
  detailLoading.value = true
  detailRecord.value = record
  try {
    detailRecord.value = await getScaleResultDetail(record.id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载报告失败'
  } finally {
    detailLoading.value = false
  }
}

const recalc = async (record: ScaleDistributionRecord) => {
  saving.value = true
  try {
    detailRecord.value = await recalculateScaleResult(record.id)
    statusMessage.value = '已重新计算'
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重新计算失败'
  } finally {
    saving.value = false
  }
}

const downloadCsv = async (unfinished = false) => {
  const file = await exportScaleResults(unfinished)
  const blob = new Blob([file.content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = file.filename
  link.click()
  URL.revokeObjectURL(url)
}

const importAnswers = async () => {
  const lines = importContent.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  const grouped = new Map<string, Array<{ questionId: string; questionType: string; myAnswer: string }>>()
  for (const line of lines.slice(1)) {
    const [recordId, questionId, questionType, myAnswer] = line.split(',').map((item) => item.trim())
    if (!recordId || !questionId || !questionType) continue
    grouped.set(recordId, [...(grouped.get(recordId) || []), { questionId, questionType, myAnswer: myAnswer || '' }])
  }
  const records = Array.from(grouped.entries()).map(([record_id, answers]) => ({ record_id, answers }))
  if (records.length === 0) {
    errorMessage.value = '没有可导入的答案行'
    return
  }
  saving.value = true
  try {
    const result = await importScaleAnswers(records)
    statusMessage.value = `已导入 ${result.imported} 条测评记录`
    importContent.value = ''
    await loadAll()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '导入答案失败'
  } finally {
    saving.value = false
  }
}

const dateText = (value?: string | null) => (value ? new Date(value).toLocaleString('zh-CN') : '--')

onMounted(async () => {
  resetSurveyForm()
  await loadAll()
})
</script>

<template>
  <div class="space-y-6">
    <Transition name="toast-slide">
      <div
        v-if="toastMessage"
        class="fixed left-1/2 top-6 z-[90] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full px-5 py-3 text-sm font-bold text-white shadow-xl"
        :class="errorMessage ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
      >
        {{ toastMessage }}
      </div>
    </Transition>

    <SectionTitle title="量表测评" description="独立管理结构化量表、分发任务、参与者答题结果与预警。" />

    <div class="grid gap-4 md:grid-cols-3">
      <BaseCard class="glass border-white/60">
        <div class="flex items-center justify-between">
          <p class="text-sm text-slate-500">量表总数</p>
          <ClipboardList class="h-5 w-5 text-primary" />
        </div>
        <p class="mt-3 text-3xl font-black text-slate-900 dark:text-white">{{ surveys.length }}</p>
      </BaseCard>
      <BaseCard class="glass border-white/60">
        <div class="flex items-center justify-between">
          <p class="text-sm text-slate-500">已发布</p>
          <CheckCircle2 class="h-5 w-5 text-emerald-500" />
        </div>
        <p class="mt-3 text-3xl font-black text-slate-900 dark:text-white">{{ publishedSurveys.length }}</p>
      </BaseCard>
      <BaseCard class="glass border-white/60">
        <div class="flex items-center justify-between">
          <p class="text-sm text-slate-500">测评记录</p>
          <FileText class="h-5 w-5 text-cyan-500" />
        </div>
        <p class="mt-3 text-3xl font-black text-slate-900 dark:text-white">{{ results.length }}</p>
      </BaseCard>
    </div>

    <BaseCard>
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex gap-2 overflow-x-auto">
          <button
            v-for="tab in [
              { key: 'surveys', label: '量表库', icon: ClipboardList },
              { key: 'distributions', label: '分发管理', icon: Send },
              { key: 'results', label: '测评结果', icon: FileText },
            ]"
            :key="tab.key"
            class="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold transition"
            :class="activeTab === tab.key ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'"
            type="button"
            @click="activeTab = tab.key as any"
          >
            <component :is="tab.icon" class="h-4 w-4" />
            {{ tab.label }}
          </button>
        </div>
        <button class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-900" type="button" @click="loadAll">
          <RefreshCw class="h-4 w-4" />
          刷新
        </button>
      </div>
    </BaseCard>

    <div v-if="activeTab === 'surveys'" class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <BaseCard>
        <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <SectionTitle title="量表库" description="发布后会固化答题 JSON，已分发记录永远读取发布快照。" />
          <button
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
            type="button"
            @click="openHuaxinyunImport"
          >
            <Upload class="h-4 w-4" />
            导入华心云 JSON
          </button>
        </div>
        <div v-if="loading" class="mt-6 text-sm text-slate-500">正在加载量表...</div>
        <div v-else class="mt-5 space-y-3">
          <div v-for="survey in surveys" :key="survey.id" class="rounded-2xl border border-slate-100 p-4 dark:border-slate-800">
            <div class="flex items-start justify-between gap-4">
              <div>
	                <div class="flex flex-wrap items-center gap-2">
	                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">{{ assessmentStatusLabel(survey.status) }}</span>
	                  <span v-if="survey.self_test_enabled" class="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-bold text-primary dark:bg-blue-950/30">自由测评</span>
	                  <span class="text-xs text-slate-400">{{ survey.question_count || survey.questions?.length || 0 }} 题</span>
	                </div>
                <h3 class="mt-2 font-bold text-slate-900 dark:text-white">{{ survey.title }}</h3>
                <p class="mt-1 text-xs text-slate-400">{{ survey.code }}</p>
              </div>
              <div class="flex gap-1">
                <button class="grid h-9 w-9 place-items-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="上移" type="button" @click="moveSurvey(survey, 'up')"><ChevronUp class="h-4 w-4" /></button>
                <button class="grid h-9 w-9 place-items-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="下移" type="button" @click="moveSurvey(survey, 'down')"><ChevronDown class="h-4 w-4" /></button>
                <button class="grid h-9 w-9 place-items-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="编辑" type="button" @click="editSurvey(survey)"><Eye class="h-4 w-4" /></button>
	                <button class="grid h-9 w-9 place-items-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="复制" type="button" @click="copySurvey(survey)"><Copy class="h-4 w-4" /></button>
	                <button class="grid h-9 w-9 place-items-center rounded-lg text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30" title="发布" type="button" @click="publishSurvey(survey)"><CheckCircle2 class="h-4 w-4" /></button>
	              </div>
	            </div>
	            <button
	              class="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-bold transition"
	              :class="survey.self_test_enabled ? 'border-blue-200 bg-blue-50 text-primary hover:bg-blue-100 dark:border-blue-900 dark:bg-blue-950/30' : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-900'"
	              type="button"
	              @click="toggleSelfTest(survey)"
	            >
	              <CheckCircle2 class="h-4 w-4" />
	              {{ survey.self_test_enabled ? '关闭自由测评' : '开放自由测评' }}
	            </button>
	          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle :title="editingSurvey ? '编辑量表' : '新建量表'" description="先用结构化 JSON 维护题目、选项、维度和结果解释；字段与后端发布快照一致。" />
        <div class="mt-5 grid gap-4">
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">标题<input v-model="form.title" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none focus:border-primary dark:border-slate-800 dark:bg-slate-900" /></label>
            <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">编码<input v-model="form.code" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none focus:border-primary dark:border-slate-800 dark:bg-slate-900" /></label>
	          </div>
	          <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">描述<textarea v-model="form.description" class="mt-2 min-h-20 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none focus:border-primary dark:border-slate-800 dark:bg-slate-900" /></label>
	          <label class="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
	            <span>
	              <span class="block">开放自由测评</span>
	              <span class="mt-1 block text-xs font-normal text-slate-400">开启后参与者可在量表测评中自主进入并生成报告。</span>
	            </span>
	            <input v-model="form.self_test_enabled" class="h-5 w-5 accent-blue-600" type="checkbox" />
	          </label>
	          <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">量表结构 JSON<textarea v-model="form.schema" class="mt-2 min-h-[420px] w-full rounded-xl border border-slate-200 bg-slate-950 px-3 py-2 font-mono text-xs leading-6 text-slate-100 outline-none focus:border-primary" spellcheck="false" /></label>
          <div class="flex flex-wrap gap-2">
            <button class="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white disabled:opacity-60" :disabled="saving" type="button" @click="saveSurvey">
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin" />
              <Plus v-else class="h-4 w-4" />
              {{ editingSurvey ? '保存量表' : '创建量表' }}
            </button>
            <button class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 dark:border-slate-800 dark:text-slate-300" type="button" @click="resetSurveyForm">重置</button>
          </div>
        </div>
      </BaseCard>
    </div>

    <div v-if="huaxinyunImportOpen" class="fixed inset-0 z-[80] overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm">
      <div class="mx-auto my-6 max-w-5xl overflow-hidden rounded-[28px] bg-white shadow-2xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-4 border-b border-slate-100 p-6 dark:border-slate-800">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.12em] text-primary/70">华心云量表导入</p>
            <h2 class="mt-1 text-2xl font-black text-slate-900 dark:text-white">导入华心云量表 JSON</h2>
            <p class="mt-2 text-sm text-slate-500">支持 all-surveys.json、单个 survey_*.json 或包含 surveyJson 的分页响应。</p>
          </div>
          <button class="grid h-10 w-10 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" type="button" @click="huaxinyunImportOpen = false"><X class="h-5 w-5 text-slate-400" /></button>
        </div>
        <div class="grid gap-5 p-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div class="space-y-4">
            <label class="block rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm font-bold text-slate-600 hover:border-primary hover:bg-blue-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-blue-950/20">
              <Upload class="mx-auto mb-2 h-6 w-6 text-primary" />
              {{ huaxinyunImportFileName || '选择 JSON 文件' }}
              <input class="hidden" accept=".json,application/json" type="file" @change="handleHuaxinyunFile" />
            </label>
            <textarea
              v-model="huaxinyunImportContent"
              class="min-h-[320px] w-full rounded-2xl border border-slate-200 bg-slate-950 p-3 font-mono text-xs leading-6 text-slate-100 outline-none focus:border-primary"
              placeholder="也可以直接粘贴华心云导出的 JSON"
              spellcheck="false"
            />
            <div class="grid gap-3">
              <label class="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-white p-4 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
                <span>
                  <span class="block">导入后立即发布</span>
                  <span class="mt-1 block text-xs font-normal text-slate-400">仅发布题目、维度、结果解释完整且公式通过预检的量表。</span>
                </span>
                <input v-model="huaxinyunImportPublish" class="h-5 w-5 accent-blue-600" type="checkbox" />
              </label>
              <label class="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-white p-4 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
                <span>
                  <span class="block">覆盖无答题记录的同编码量表</span>
                  <span class="mt-1 block text-xs font-normal text-slate-400">已有答题记录时始终跳过，避免影响历史报告。</span>
                </span>
                <input v-model="huaxinyunImportOverwrite" class="h-5 w-5 accent-blue-600" type="checkbox" />
              </label>
              <label class="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-white p-4 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
                <span>
                  <span class="block">跳过异常量表继续导入</span>
                  <span class="mt-1 block text-xs font-normal text-slate-400">关闭后遇到第一条异常会中断导入。</span>
                </span>
                <input v-model="huaxinyunImportSkipInvalid" class="h-5 w-5 accent-blue-600" type="checkbox" />
              </label>
            </div>
            <div class="flex flex-wrap gap-2">
              <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 disabled:opacity-60 dark:border-slate-800 dark:text-slate-300" :disabled="huaxinyunImportLoading" type="button" @click="runHuaxinyunImport(true)">
                <Loader2 v-if="huaxinyunImportLoading" class="h-4 w-4 animate-spin" />
                <Eye v-else class="h-4 w-4" />
                先预检
              </button>
              <button class="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white disabled:opacity-60" :disabled="huaxinyunImportLoading" type="button" @click="runHuaxinyunImport(false)">
                <Loader2 v-if="huaxinyunImportLoading" class="h-4 w-4 animate-spin" />
                <Upload v-else class="h-4 w-4" />
                执行导入
              </button>
            </div>
          </div>
          <div class="rounded-3xl border border-slate-100 p-5 dark:border-slate-800">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h3 class="font-bold text-slate-900 dark:text-white">预检与导入结果</h3>
                <p class="mt-1 text-xs text-slate-400">异常会逐条列出，便于回到 JSON 或量表编辑器修正。</p>
              </div>
              <span v-if="huaxinyunImportResult" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-primary dark:bg-blue-950/30">{{ huaxinyunImportResult.total }} 份</span>
            </div>
            <div v-if="huaxinyunImportResult" class="mt-5 grid grid-cols-2 gap-3 text-sm">
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
                <p class="text-xs text-slate-400">可导入</p>
                <p class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ huaxinyunImportResult.importable }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
                <p class="text-xs text-slate-400">可发布</p>
                <p class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ huaxinyunImportResult.publishable }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
                <p class="text-xs text-slate-400">新增/更新</p>
                <p class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ huaxinyunImportResult.imported + huaxinyunImportResult.updated }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
                <p class="text-xs text-slate-400">跳过/失败</p>
                <p class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ huaxinyunImportResult.skipped + huaxinyunImportResult.failed }}</p>
              </div>
            </div>
            <div class="mt-5 max-h-[460px] space-y-3 overflow-y-auto pr-1">
              <div v-for="item in huaxinyunImportResult?.items || []" :key="item.code" class="rounded-2xl border border-slate-100 p-4 text-sm dark:border-slate-800">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <h4 class="font-bold text-slate-900 dark:text-white">{{ item.title }}</h4>
                    <p class="mt-1 text-xs text-slate-400">{{ item.code }} · {{ item.question_count }} 题 · {{ item.dimension_count }} 维度 · {{ item.result_count }} 结果</p>
                  </div>
                  <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="item.can_import ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-200'">{{ item.action || (item.can_import ? '可导入' : '异常') }}</span>
                </div>
                <ul v-if="item.issues.length" class="mt-3 space-y-1 rounded-xl bg-rose-50 p-3 text-xs leading-5 text-rose-700 dark:bg-rose-950/30 dark:text-rose-200">
                  <li v-for="issue in item.issues" :key="issue">{{ issue }}</li>
                </ul>
                <ul v-if="item.warnings.length" class="mt-3 space-y-1 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-700 dark:bg-amber-950/30 dark:text-amber-200">
                  <li v-for="warning in item.warnings" :key="warning">{{ warning }}</li>
                </ul>
              </div>
              <p v-if="!huaxinyunImportResult" class="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-500 dark:bg-slate-900">请选择文件后先预检。</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'distributions'" class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <BaseCard>
        <SectionTitle title="创建分发" description="本期完整开放量表类型；神经心理测评只预留类型，不生成任务。" />
        <div class="mt-5 space-y-4">
          <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">分发主题<input v-model="distributionForm.title" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none focus:border-primary dark:border-slate-800 dark:bg-slate-900" /></label>
          <div>
            <p class="text-sm font-semibold text-slate-600 dark:text-slate-300">测评类型</p>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <button class="rounded-xl border px-3 py-3 text-sm font-bold" :class="distributionForm.assessment_category === 'scale' ? 'border-primary bg-blue-50 text-primary' : 'border-slate-200 text-slate-500 dark:border-slate-800'" type="button" @click="distributionForm.assessment_category = 'scale'">量表类型</button>
              <button class="rounded-xl border px-3 py-3 text-sm font-bold" :class="distributionForm.assessment_category === 'neuropsych' ? 'border-amber-400 bg-amber-50 text-amber-700' : 'border-slate-200 text-slate-500 dark:border-slate-800'" type="button" @click="distributionForm.assessment_category = 'neuropsych'">神经心理测评（后续开发）</button>
            </div>
          </div>
          <div class="grid gap-2">
            <p class="text-sm font-semibold text-slate-600 dark:text-slate-300">选择量表</p>
            <button v-for="survey in publishedSurveys" :key="survey.id" class="flex items-center justify-between rounded-xl border px-3 py-2 text-left text-sm" :class="distributionForm.survey_ids.includes(survey.id) ? 'border-primary bg-blue-50 text-primary' : 'border-slate-200 dark:border-slate-800'" type="button" @click="distributionForm.survey_ids = toggleSelected(distributionForm.survey_ids, survey.id)">
              <span>{{ survey.title }}</span><CheckCircle2 v-if="distributionForm.survey_ids.includes(survey.id)" class="h-4 w-4" />
            </button>
            <p v-if="publishedSurveys.length === 0" class="rounded-xl bg-slate-50 p-3 text-sm text-slate-500 dark:bg-slate-900">暂无已发布量表。</p>
          </div>
          <div class="grid gap-2">
            <p class="text-sm font-semibold text-slate-600 dark:text-slate-300">选择参与者</p>
            <div class="max-h-56 space-y-2 overflow-y-auto rounded-xl border border-slate-100 p-2 dark:border-slate-800">
              <button v-for="patient in patients" :key="patient.id" class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm" :class="distributionForm.user_ids.includes(patient.id) ? 'bg-blue-50 text-primary dark:bg-blue-950/30' : 'hover:bg-slate-50 dark:hover:bg-slate-900'" type="button" @click="distributionForm.user_ids = toggleSelected(distributionForm.user_ids, patient.id)">
                <span>{{ patient.full_name || patient.username }}</span><CheckCircle2 v-if="distributionForm.user_ids.includes(patient.id)" class="h-4 w-4" />
              </button>
            </div>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">开始时间<input v-model="distributionForm.start_at" type="datetime-local" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none dark:border-slate-800 dark:bg-slate-900" /></label>
            <label class="text-sm font-semibold text-slate-600 dark:text-slate-300">结束时间<input v-model="distributionForm.end_at" type="datetime-local" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none dark:border-slate-800 dark:bg-slate-900" /></label>
          </div>
          <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white disabled:opacity-60" :disabled="saving || distributionForm.assessment_category === 'neuropsych'" type="button" @click="createDistribution">
            <Send class="h-4 w-4" />
            创建分发计划
          </button>
        </div>
      </BaseCard>

      <BaseCard>
        <SectionTitle title="分发计划" description="跟踪主题、任务数、完成数和有效期。" />
        <div class="mt-5 space-y-3">
          <div v-for="plan in plans" :key="plan.id" class="rounded-2xl border border-slate-100 p-4 dark:border-slate-800">
            <div class="flex items-start justify-between gap-4">
              <div>
                <h3 class="font-bold text-slate-900 dark:text-white">{{ plan.title }}</h3>
                <p class="mt-1 text-xs text-slate-400">{{ plan.assessment_category === 'scale' ? '量表类型' : '神经心理测评' }} · {{ assessmentStatusLabel(plan.status) }}</p>
                <p class="mt-2 text-sm text-slate-500">完成 {{ plan.completed_count || 0 }} / {{ plan.record_count || 0 }}</p>
              </div>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">{{ dateText(plan.created_at) }}</span>
            </div>
          </div>
          <p v-if="plans.length === 0" class="rounded-2xl bg-slate-50 p-5 text-center text-sm text-slate-500 dark:bg-slate-900">暂无分发计划。</p>
        </div>
      </BaseCard>
    </div>

    <BaseCard v-if="activeTab === 'results'">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <SectionTitle title="测评结果" description="查看参与者答题状态、计算状态、报告和预警。" />
        <div class="flex gap-2">
          <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 dark:border-slate-800 dark:text-slate-300" type="button" @click="downloadCsv(false)"><Download class="h-4 w-4" />导出结果</button>
          <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 dark:border-slate-800 dark:text-slate-300" type="button" @click="downloadCsv(true)"><Download class="h-4 w-4" />未完成名单</button>
        </div>
      </div>
      <div class="mt-5 overflow-x-auto">
        <table class="w-full min-w-[860px] text-left text-sm">
          <thead class="text-xs uppercase tracking-[0.12em] text-slate-400">
	            <tr><th class="py-3">参与者</th><th>量表</th><th>来源</th><th>主题</th><th>状态</th><th>计算</th><th>总分</th><th>预警</th><th>完成时间</th><th class="text-right">操作</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-for="record in results" :key="record.id" class="text-slate-700 dark:text-slate-200">
	              <td class="py-4 font-semibold">{{ record.patient_name || record.patient_username }}</td>
	              <td>{{ record.survey_title }}</td>
	              <td>{{ record.source_type === 'self' ? '自由测评' : '管理员分发' }}</td>
	              <td>{{ record.plan_title }}</td>
              <td>{{ assessmentStatusLabel(record.status) }}</td>
              <td>{{ assessmentStatusLabel(record.calc_status) }}</td>
              <td>{{ record.total_score ?? '--' }}</td>
              <td><span :class="['rounded-full px-2 py-1 text-xs font-bold', warningClass(record.warning_level)]">{{ warningText[record.warning_level] }}</span></td>
              <td>{{ dateText(record.completed_at) }}</td>
              <td class="text-right">
                <button class="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-primary hover:bg-blue-50 dark:hover:bg-blue-950/30" type="button" @click="openResult(record)">
                  <Eye class="h-4 w-4" />详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="results.length === 0" class="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500 dark:bg-slate-900">暂无测评结果。</p>
      </div>
      <div class="mt-6 rounded-3xl border border-slate-100 p-5 dark:border-slate-800">
        <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 class="font-bold text-slate-900 dark:text-white">线下答案导入</h3>
            <p class="mt-1 text-xs text-slate-400">CSV 表头：record_id,question_id,question_type,my_answer。多题答案按 record_id 自动合并后计算。</p>
          </div>
          <button class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white disabled:opacity-60 dark:bg-white dark:text-slate-900" :disabled="saving" type="button" @click="importAnswers">
            <Download class="h-4 w-4 rotate-180" />
            导入并计算
          </button>
        </div>
        <textarea v-model="importContent" class="mt-4 min-h-32 w-full rounded-2xl border border-slate-200 bg-white p-3 font-mono text-xs outline-none focus:border-primary dark:border-slate-800 dark:bg-slate-900" placeholder="record_id,question_id,question_type,my_answer" />
      </div>
    </BaseCard>

    <div v-if="detailRecord" class="fixed inset-0 z-[80] overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm">
      <div class="mx-auto my-6 max-w-5xl overflow-hidden rounded-[28px] bg-white shadow-2xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-4 border-b border-slate-100 p-6 dark:border-slate-800">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.12em] text-primary/70">量表测评结果</p>
            <h2 class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ detailRecord.survey_title }}</h2>
	            <p class="mt-2 text-sm text-slate-500">{{ detailRecord.patient_name }} · {{ detailRecord.source_type === 'self' ? '自由测评' : detailRecord.plan_title }}</p>
          </div>
          <button class="grid h-10 w-10 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" type="button" @click="detailRecord = null"><X class="h-5 w-5 text-slate-400" /></button>
        </div>
        <div v-if="detailLoading" class="flex justify-center p-12 text-slate-500"><Loader2 class="mr-2 h-5 w-5 animate-spin" />加载报告...</div>
        <div v-else class="grid gap-5 p-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div class="rounded-3xl bg-slate-50 p-5 dark:bg-slate-900">
            <Brain class="h-8 w-8 text-primary" />
            <p class="mt-4 text-sm text-slate-500">总分</p>
            <p class="mt-2 text-5xl font-black text-slate-900 dark:text-white">{{ detailRecord.total_score ?? '--' }}</p>
            <span :class="['mt-4 inline-flex rounded-full px-3 py-1 text-xs font-bold', warningClass(detailRecord.warning_level)]">{{ warningText[detailRecord.warning_level] }}</span>
            <button class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 hover:bg-white dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-950" type="button" @click="recalc(detailRecord)">
              <RefreshCw class="h-4 w-4" />重新计算
            </button>
            <p v-if="detailRecord.calc_error" class="mt-4 rounded-2xl bg-rose-50 p-3 text-sm text-rose-600 dark:bg-rose-950/30 dark:text-rose-200"><AlertTriangle class="mb-2 h-4 w-4" />{{ detailRecord.calc_error }}</p>
          </div>
          <div class="space-y-4">
            <div v-for="dimension in detailRecord.report?.dimensions || detailRecord.dimensions || []" :key="dimension.dimensionId || dimension.id" class="rounded-3xl border border-slate-100 p-5 dark:border-slate-800">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-slate-900 dark:text-white">{{ dimension.name || dimension.dimension_name }}</h3>
                <span :class="['rounded-full px-3 py-1 text-xs font-bold', warningClass(dimension.warningLevel || dimension.warning_level)]">{{ warningLabel(dimension.warningLevel || dimension.warning_level) }}</span>
              </div>
              <p class="mt-3 text-sm text-slate-500">原始分 {{ dimension.rawScore ?? dimension.raw_score ?? 0 }} / 标准分 {{ dimension.standardScore ?? dimension.standard_score ?? 0 }}</p>
              <p v-if="dimension.conclusion" class="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-300">{{ dimension.conclusion }}</p>
              <p v-if="dimension.suggestion" class="mt-2 rounded-2xl bg-blue-50 p-3 text-sm leading-7 text-blue-700 dark:bg-blue-950/30 dark:text-blue-200">{{ dimension.suggestion }}</p>
            </div>
            <div class="rounded-3xl border border-slate-100 p-5 dark:border-slate-800">
              <h3 class="font-bold text-slate-900 dark:text-white">原始答案</h3>
              <div class="mt-3 max-h-64 space-y-2 overflow-y-auto text-sm">
                <div v-for="answer in detailRecord.answers || []" :key="answer.id" class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
                  {{ answer.question_id }} · {{ answer.answer_text || answer.my_answer }} · {{ answer.score ?? 0 }}分
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
