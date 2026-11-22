<script setup lang="ts">
import {
  Activity,
  Brain,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  Eye,
  FileText,
  HeartPulse,
  KeyRound,
  MessageSquare,
  Mic,
  Plus,
  Search,
  Trash2,
  Video,
} from 'lucide-vue-next'
import { computed, onUnmounted, ref, watch } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import {
  createVerificationCode,
  deleteVerificationCode,
  getAllProfiles,
  getAssessments,
  getEmotionDiaries,
  getPatientInterventionPlan,
  getVerificationCodes,
  type DoctorVerificationCode,
} from '@/db/api'
import { resolveAvatarSource } from '@/lib/avatar-presets'
import type { Assessment, EmotionDiary, Profile } from '@/types'

type PatientTab = 'package' | 'scale' | 'voice' | 'expression' | 'conversation' | 'intervention'

interface PatientDetails {
  diaries: EmotionDiary[]
  assessments: Assessment[]
  interventions?: any
}

const loading = ref(true)
const loadingDetails = ref(false)
const profiles = ref<Profile[]>([])
const searchQuery = ref('')
const detailDialogOpen = ref(false)
const codeManagerOpen = ref(false)
const selectedPatient = ref<Profile | null>(null)
const patientDetails = ref<PatientDetails | null>(null)
const activePatientTab = ref<PatientTab>('package')
const expandedPanels = ref<Record<string, boolean>>({})
const statusMessage = ref('')
const errorMessage = ref('')

const verificationCodes = ref<DoctorVerificationCode[]>([])
const loadingCodes = ref(false)
const creatingCode = ref(false)
const codeForm = ref({
  code: '',
  notes: '',
})
const copiedCodeId = ref<string | null>(null)
const toastMessage = computed(() => errorMessage.value || statusMessage.value)
const toastTone = computed(() => (errorMessage.value ? 'error' : 'success'))
let toastTimer: number | null = null

watch(toastMessage, (message) => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  if (!message) {
    toastTimer = null
    return
  }
  toastTimer = window.setTimeout(() => {
    statusMessage.value = ''
    errorMessage.value = ''
    toastTimer = null
  }, 2200)
})

const filteredPatients = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  return profiles.value
    .filter((item) => item.role === 'user' || item.role === 'doctor' || item.role === 'admin')
    .filter((item) => {
      if (!keyword) return true
      return (
        item.username.toLowerCase().includes(keyword) ||
        (item.full_name || '').toLowerCase().includes(keyword) ||
        (item.department_name || '').toLowerCase().includes(keyword)
      )
    })
})

const detailsAssessments = computed(() => patientDetails.value?.assessments || [])
const interventionPlans = computed(() => patientDetails.value?.interventions?.plans || [])
const packageAssessments = computed(() =>
  detailsAssessments.value.filter((item) => item.assessment_type === 'assessment_package_report'),
)
const scaleAssessments = computed(() =>
  detailsAssessments.value.filter(
    (item) => Boolean(getScaleData(item)) || item.assessment_type?.includes('fusion') || item.assessment_type?.includes('scale') || item.assessment_type === 'assessment_package_report',
  ),
)
const voiceAssessments = computed(() =>
  detailsAssessments.value.filter(
    (item) => Boolean(getVoiceData(item)) || item.assessment_type?.includes('voice') || item.assessment_type?.includes('fusion') || item.assessment_type === 'assessment_package_report',
  ),
)
const expressionAssessments = computed(() =>
  detailsAssessments.value.filter(
    (item) => Boolean(getExpressionData(item)) || item.assessment_type?.includes('expression') || item.assessment_type?.includes('fusion') || item.assessment_type === 'assessment_package_report',
  ),
)
const conversationAssessments = computed(() =>
  detailsAssessments.value.filter((item) => getConversationHistory(item).length > 0),
)

const getScaleData = (assessment: Assessment) =>
  assessment.report?.scaleData ?? assessment.report?.scale_data ?? null

const getVoiceData = (assessment: Assessment) => {
  const voice = assessment.report?.voiceData ?? assessment.report?.voice_data ?? null
  if (!voice) return null
  const base = voice.reportData ? { ...voice.reportData, duration: voice.duration, waveform: voice.waveform } : voice
  const emotions = base.emotions || base.emotion_vector || base.emotionVector || {}
  const speechMetrics = base.speech_metrics || base.speechMetrics || {}
  const sadRisk = Math.round(((emotions.sad ?? 0) + (emotions.fearful ?? emotions.fear ?? 0)) * 50)
  const indicatorRisk = base.indicators
    ? [base.indicators.isLowSpeed, base.indicators.isHighPitchDrop, base.indicators.isLongPause].filter(Boolean).length * 12
    : 0
  const score = base.score ?? base.risk_score ?? base.emotion_score ?? Math.min(100, Math.max(0, sadRisk + indicatorRisk))
  return {
    ...base,
    score,
    speech_rate: base.speech_rate ?? (Number(speechMetrics.speed || 0) || undefined),
    pitch_variation: base.pitch_variation ?? (Number(speechMetrics.tone || 0) || undefined),
    pause_frequency: base.pause_frequency ?? (Number(speechMetrics.pause || 0) || undefined),
    volume_stability: base.volume_stability ?? (Number(speechMetrics.energy || 0) || undefined),
    analysis: base.analysis ?? base.depression_analysis ?? base.depressionAnalysis,
    emotions: {
      calm: emotions.calm ?? 0,
      happy: emotions.happy ?? 0,
      sad: emotions.sad ?? 0,
      angry: emotions.angry ?? 0,
      fear: emotions.fear ?? emotions.fearful ?? 0,
      surprise: emotions.surprise ?? emotions.surprised ?? 0,
    },
  }
}

const getExpressionData = (assessment: Assessment) => {
  const expression = assessment.report?.expressionData ?? assessment.report?.expression_data ?? null
  if (!expression) return null
  const base = expression.reportData ?? expression
  return {
    ...base,
    depression_risk_score: base.depression_risk_score ?? base.risk_score ?? 0,
    risk_score: base.risk_score ?? base.depression_risk_score ?? 0,
    facial_expressions: base.facial_expressions || base.emotion_radar || {},
    micro_features: base.micro_features || base.micro_expressions || {},
  }
}

const getConversationHistory = (assessment: Assessment) =>
  assessment.conversation_history?.length
    ? assessment.conversation_history
    : assessment.report?.scaleData?.conversationHistory || assessment.report?.scaleData?.conversation_history || []

const resetMessages = () => {
  statusMessage.value = ''
  errorMessage.value = ''
}

const loadPatients = async () => {
  loading.value = true
  resetMessages()
  try {
    profiles.value = await getAllProfiles()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载用户失败'
  } finally {
    loading.value = false
  }
}

const loadPatientDetails = async (patient: Profile) => {
  selectedPatient.value = patient
  patientDetails.value = null
  detailDialogOpen.value = true
  activePatientTab.value = 'scale'
  expandedPanels.value = {}
  loadingDetails.value = true
  resetMessages()
  try {
    const [diaries, assessments, interventions] = await Promise.all([
      getEmotionDiaries(patient.id, 30),
      getAssessments(patient.id, 80),
      getPatientInterventionPlan(patient.id).catch(() => ({ plans: [] })),
    ])
    patientDetails.value = { diaries, assessments, interventions }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载患者详情失败'
  } finally {
    loadingDetails.value = false
  }
}

const togglePanel = (key: string) => {
  expandedPanels.value = {
    ...expandedPanels.value,
    [key]: !expandedPanels.value[key],
  }
}

const riskBadgeClass = (riskLevel?: number | null) => {
  if ((riskLevel || 0) >= 80) return 'bg-rose-500 text-white'
  if ((riskLevel || 0) >= 60) return 'bg-orange-500 text-white'
  if ((riskLevel || 0) >= 40) return 'bg-amber-500 text-white'
  return 'bg-emerald-500 text-white'
}

const riskText = (riskLevel?: number | null) => {
  if ((riskLevel || 0) >= 80) return '极高风险'
  if ((riskLevel || 0) >= 60) return '高风险'
  if ((riskLevel || 0) >= 40) return '中风险'
  return '低风险'
}

const packageBody = (assessment: Assessment) => assessment.report || {}

const packageSections = (assessment: Assessment) => {
  const report = packageBody(assessment)
  if (Array.isArray(report.sections) && report.sections.length) return report.sections
  const legacy = [
    { type: 'scale', title: '量表测评', data: report.scaleData },
    { type: 'neuropsych', title: '神经心理测验', data: report.neuropsychData },
    { type: 'dialogue_scale', title: '对话式心理健康评估', data: report.dialogueData },
    { type: 'voice', title: '语音识别', data: report.voiceData },
    { type: 'expression', title: '表情评估', data: report.expressionData },
  ]
  return legacy
    .filter((item) => item.data && Object.keys(item.data).length > 0)
    .map((item) => ({
      type: item.type,
      title: item.title,
      score: item.data.score ?? item.data.totalScore ?? 0,
      riskLevel: item.data.riskLevel || item.data.warningLevel || item.data.warning_level || 'none',
      summary: item.data.summary || item.data.overall?.summary || '该模块已完成。',
      items: (Array.isArray(item.data.reports) ? item.data.reports : [item.data]).map((report: any, index: number) => ({
        title: report.surveyTitle || report.testTitle || report.title || `${item.title} ${index + 1}`,
        score: report.score ?? report.totalScore ?? 0,
        riskLevel: report.riskLevel || report.warningLevel || report.warning_level || 'none',
        summary: report.summary || report.conclusion || '该测评已完成。',
        keyFindings: report.keyFindings || [],
        suggestions: report.suggestions || [],
        metrics: report.metrics || {},
      })),
    }))
}

const moduleTitle = (type?: string) => {
  if (type === 'scale') return '量表测评'
  if (type === 'neuropsych') return '神经心理测验'
  if (type === 'dialogue_scale') return '对话式心理健康评估'
  if (type === 'voice') return '语音识别'
  if (type === 'expression') return '表情评估'
  if (type === 'multimodal_baseline') return '多模态基线'
  return '测评项目'
}

const warningText = (risk?: string) => {
  if (risk === 'high') return '高风险'
  if (risk === 'middle' || risk === 'medium') return '中风险'
  if (risk === 'low') return '低风险'
  return '低风险'
}

const warningClass = (risk?: string) => {
  if (risk === 'high') return 'bg-rose-100 text-rose-700'
  if (risk === 'middle' || risk === 'medium') return 'bg-amber-100 text-amber-700'
  if (risk === 'low') return 'bg-emerald-100 text-emerald-700'
  return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-200'
}

const asTextList = (value: any) => Array.isArray(value) ? value.filter(Boolean).map(String) : []

const metricEntries = (metrics: any) =>
  Object.entries(metrics || {})
    .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '')
    .slice(0, 6)

const roleBadgeClass = (role: string) => {
  if (role === 'doctor') return 'bg-emerald-100 text-emerald-700'
  if (role === 'admin') return 'bg-emerald-100 text-emerald-700'
  if (role === 'super_admin') return 'bg-purple-100 text-purple-700'
  return 'bg-blue-100 text-blue-700'
}

const roleText = (role: string) => {
  if (role === 'super_admin') return '超级管理员'
  if (role === 'doctor' || role === 'admin') return '管理员'
  return '用户'
}

const avatarDisplay = (profile: Profile) => {
  const avatarSource = resolveAvatarSource(profile.avatar_url)
  return {
    imageUrl: avatarSource.imageUrl,
    preset: avatarSource.preset,
    fallback: profile.username.charAt(0).toUpperCase(),
  }
}

const formatConversationMessage = (message: any) => {
  if (typeof message?.content === 'string') return message.content
  if (Array.isArray(message?.content)) {
    return message.content
      .filter((item: any) => item.type === 'text')
      .map((item: any) => item.text)
      .join('')
  }
  return JSON.stringify(message?.content || '')
}

const loadVerificationCodes = async (resetNotice = false) => {
  loadingCodes.value = true
  if (resetNotice) resetMessages()
  try {
    verificationCodes.value = await getVerificationCodes()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载验证码失败'
  } finally {
    loadingCodes.value = false
  }
}

const openCodeManager = async () => {
  codeManagerOpen.value = true
  await loadVerificationCodes(true)
}

const createCode = async () => {
  if (!codeForm.value.code.trim()) {
    errorMessage.value = '请输入验证码'
    return
  }
  if (!/^[a-zA-Z0-9]+$/.test(codeForm.value.code.trim())) {
    errorMessage.value = '验证码只能包含字母和数字'
    return
  }
  creatingCode.value = true
  resetMessages()
  try {
    await createVerificationCode(codeForm.value.code.trim(), codeForm.value.notes.trim() || undefined)
    statusMessage.value = '验证码创建成功'
    codeForm.value = { code: '', notes: '' }
    await loadVerificationCodes()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建验证码失败'
  } finally {
    creatingCode.value = false
  }
}

const removeCode = async (id: string, code: string) => {
  if (!window.confirm(`确定删除验证码“${code}”吗？`)) return
  resetMessages()
  try {
    await deleteVerificationCode(id)
    statusMessage.value = '验证码已删除'
    await loadVerificationCodes()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除验证码失败'
  }
}

const copyCode = async (id: string, code: string) => {
  try {
    await navigator.clipboard.writeText(code)
    copiedCodeId.value = id
    statusMessage.value = '验证码已复制'
    window.setTimeout(() => {
      copiedCodeId.value = null
    }, 2000)
  } catch {
    errorMessage.value = '复制失败'
  }
}

void loadPatients()

onUnmounted(() => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="space-y-6">
    <Transition name="toast-slide">
      <div
        v-if="toastMessage"
        data-testid="doctor-patients-toast"
        :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
        class="fixed left-1/2 top-6 z-[80] max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-full px-5 py-3 text-sm font-medium text-white shadow-xl"
      >
        {{ toastMessage }}
      </div>
    </Transition>

    <SectionTitle title="用户管理" description="搜索用户、查看评估详情，并管理管理员验证码。" />

    <div class="flex gap-2">
      <div class="group relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-primary" />
        <input
          v-model="searchQuery"
          data-testid="patient-search-input"
          class="h-11 w-full rounded-[8px] border border-slate-200 bg-white pl-10 pr-4 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="搜索姓名或用户名..."
        />
      </div>
      <button
        data-testid="open-code-manager"
        class="inline-flex h-11 items-center gap-2 rounded-[8px] border border-slate-200 px-4 text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200"
        type="button"
        @click="openCodeManager"
      >
        <KeyRound class="h-4 w-4" />
        验证码管理
      </button>
    </div>

    <BaseCard>
      <div class="mb-5 flex items-center justify-between gap-4">
        <h2 class="text-lg font-bold text-slate-900 dark:text-white">用户列表 ({{ filteredPatients.length }})</h2>
      </div>

      <div v-if="loading" class="space-y-3">
        <div v-for="index in 5" :key="index" class="h-20 rounded-[8px] bg-slate-100 dark:bg-slate-800" />
      </div>

      <div v-else-if="filteredPatients.length === 0" class="py-12 text-center text-slate-500">
        未找到用户
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="patient in filteredPatients"
          :key="patient.id"
          class="flex flex-col gap-4 rounded-[8px] border border-slate-200 p-4 transition hover:border-primary/40 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="flex items-center gap-4">
              <div class="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-primary/10 text-primary">
                <img v-if="avatarDisplay(patient).imageUrl" :src="avatarDisplay(patient).imageUrl || undefined" alt="头像" class="h-full w-full object-cover" />
                <div v-else-if="avatarDisplay(patient).preset" :class="['flex h-full w-full items-center justify-center text-xl text-white', avatarDisplay(patient).preset?.bg]">
                  {{ avatarDisplay(patient).preset?.emoji }}
                </div>
                <span v-else class="text-base font-bold">{{ avatarDisplay(patient).fallback }}</span>
              </div>
              <div class="flex-1">
                <div class="mb-1 flex flex-wrap items-center gap-2">
                  <span class="font-bold text-slate-800 dark:text-slate-200">{{ patient.full_name || patient.username }}</span>
                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    @{{ patient.username }}
                  </span>
                  <span :class="['rounded-full px-2 py-0.5 text-[10px] font-medium', roleBadgeClass(patient.role)]">
                    {{ roleText(patient.role) }}
                  </span>
                </div>
                <div class="flex items-center gap-2 text-xs text-slate-400">
                  <span v-if="patient.gender">{{ patient.gender }}</span>
                  <span v-if="patient.gender" class="h-1 w-1 rounded-full bg-slate-300" />
                  <span>部门 {{ patient.department_name || '未分部门' }}</span>
                  <span class="h-1 w-1 rounded-full bg-slate-300" />
                  <span>注册于 {{ new Date(patient.created_at).toLocaleDateString('zh-CN') }}</span>
                </div>
              </div>
            </div>

            <button
              data-testid="patient-view-detail"
              class="inline-flex h-10 items-center justify-center gap-2 rounded-[8px] border border-slate-200 px-4 text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200"
              type="button"
              @click="loadPatientDetails(patient)"
            >
              <Eye class="h-4 w-4" />
              查看详情
            </button>
          </div>
        </div>
      </div>
    </BaseCard>

    <div
      v-if="detailDialogOpen && selectedPatient"
      data-testid="patient-detail-dialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 py-6"
      @click.self="detailDialogOpen = false"
    >
      <div class="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-[8px] bg-white shadow-xl dark:bg-slate-900">
        <div class="border-b border-slate-200 px-5 pb-3 pt-5 dark:border-slate-800">
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="text-xl font-bold text-slate-900 dark:text-white">用户详情</h3>
              <p class="mt-1 text-sm text-slate-500">查看用户基本信息、量表评估、语音情绪、表情识别和对话记录。</p>
            </div>
            <button class="rounded-[8px] border border-slate-200 px-3 py-2 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-300" type="button" @click="detailDialogOpen = false">
              关闭
            </button>
          </div>
        </div>

        <div class="border-b border-slate-200 bg-slate-50/70 px-5 py-4 dark:border-slate-800 dark:bg-slate-950/60">
          <div class="flex items-center gap-4">
            <div class="flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-primary/10 text-primary shadow-sm">
              <img v-if="avatarDisplay(selectedPatient).imageUrl" :src="avatarDisplay(selectedPatient).imageUrl || undefined" alt="头像" class="h-full w-full object-cover" />
              <div v-else-if="avatarDisplay(selectedPatient).preset" :class="['flex h-full w-full items-center justify-center text-2xl text-white', avatarDisplay(selectedPatient).preset?.bg]">
                {{ avatarDisplay(selectedPatient).preset?.emoji }}
              </div>
              <span v-else class="text-lg font-bold">{{ avatarDisplay(selectedPatient).fallback }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="mb-1 flex flex-wrap items-center gap-2">
                <h4 class="truncate text-lg font-bold text-slate-900 dark:text-white">{{ selectedPatient.full_name || selectedPatient.username }}</h4>
                <span :class="['rounded-full px-2 py-0.5 text-xs font-medium', roleBadgeClass(selectedPatient.role)]">
                  {{ roleText(selectedPatient.role) }}
                </span>
                <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {{ selectedPatient.department_name || '未分部门' }}
                </span>
              </div>
              <p class="text-sm text-slate-500">@{{ selectedPatient.username }}</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-4 gap-2 border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <div class="text-center">
            <div class="text-lg font-black text-blue-600">{{ patientDetails?.diaries?.length ?? 0 }}</div>
            <div class="text-[10px] text-slate-400">情绪日记</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-black text-purple-600">{{ detailsAssessments.length }}</div>
            <div class="text-[10px] text-slate-400">评估总数</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-black text-cyan-600">{{ packageAssessments.length }}</div>
            <div class="text-[10px] text-slate-400">综合报告</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-black text-indigo-600">{{ conversationAssessments.length }}</div>
            <div class="text-[10px] text-slate-400">对话记录</div>
          </div>
        </div>

        <div v-if="loadingDetails" class="flex-1 overflow-auto px-5 py-6">
          <div class="space-y-3">
            <div v-for="index in 3" :key="index" class="h-16 rounded-[8px] bg-slate-100 dark:bg-slate-800" />
          </div>
        </div>

        <template v-else>
          <div class="flex flex-wrap gap-2 px-5 pb-0 pt-4">
            <button
              v-for="tab in [
                { key: 'package', label: '综合测评报告', icon: Brain, count: packageAssessments.length },
                { key: 'scale', label: '量表评估', icon: FileText, count: scaleAssessments.length },
                { key: 'voice', label: '语音情绪', icon: Mic, count: voiceAssessments.length },
                { key: 'expression', label: '表情识别', icon: Video, count: expressionAssessments.length },
                { key: 'conversation', label: '对话记录', icon: MessageSquare, count: conversationAssessments.length },
                { key: 'intervention', label: '干预计划', icon: HeartPulse, count: interventionPlans.length },
              ]"
              :key="tab.key"
              :data-testid="`patient-tab-${tab.key}`"
              class="inline-flex items-center gap-2 rounded-[8px] px-3 py-2 text-sm font-semibold transition"
              :class="activePatientTab === tab.key ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'"
              type="button"
              @click="activePatientTab = tab.key as PatientTab"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
              <span v-if="tab.count > 0" class="rounded-full bg-white/20 px-1.5 py-0.5 text-[10px] dark:bg-slate-900/20">{{ tab.count }}</span>
            </button>
          </div>

          <div class="flex-1 overflow-auto px-5 pb-5 pt-4">
            <div v-if="activePatientTab === 'package'" class="space-y-4">
              <div v-if="packageAssessments.length === 0" class="py-12 text-center text-slate-500">
                <Brain class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无任务报告
              </div>
              <div v-for="assessment in packageAssessments" :key="assessment.id" class="overflow-hidden rounded-[12px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                <button
                  class="flex w-full items-center justify-between gap-4 p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
                  type="button"
                  @click="togglePanel(`package-${assessment.id}`)"
                >
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 items-center justify-center rounded-[8px] bg-cyan-100 text-cyan-700">
                      <Brain class="h-4 w-4" />
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">
                          {{ assessment.report?.packageData?.reportTitle || assessment.report?.packageData?.title || '测评任务报告' }}
                        </span>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', riskBadgeClass(assessment.risk_level)]">
                          {{ riskText(assessment.risk_level) }}
                        </span>
                      </div>
                      <p class="mt-1 text-xs text-slate-400">
                        {{ assessment.report?.packageData?.title || '测评任务' }} · {{ new Date(assessment.created_at).toLocaleString('zh-CN') }}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <div class="text-right">
                      <div class="text-xl font-black text-slate-800 dark:text-slate-200">{{ assessment.score ?? assessment.report?.overall?.score ?? 0 }}</div>
                      <div class="text-[10px] text-slate-400">综合分</div>
                    </div>
                    <ChevronUp v-if="expandedPanels[`package-${assessment.id}`]" class="h-4 w-4 text-slate-400" />
                    <ChevronDown v-else class="h-4 w-4 text-slate-400" />
                  </div>
                </button>
                <div v-if="expandedPanels[`package-${assessment.id}`]" class="border-t border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                  <div class="grid gap-3 md:grid-cols-3">
                    <div class="rounded-[10px] bg-white p-4 dark:bg-slate-900">
                      <p class="text-xs text-slate-400">任务类型</p>
                      <p class="mt-1 text-sm font-black text-slate-900 dark:text-white">{{ assessment.report?.packageData?.taskType === 'initial_screening' ? '职务犯罪初筛' : '测评任务' }}</p>
                    </div>
                    <div class="rounded-[10px] bg-white p-4 dark:bg-slate-900">
                      <p class="text-xs text-slate-400">完成项目</p>
                      <p class="mt-1 text-sm font-black text-slate-900 dark:text-white">{{ assessment.report?.packageData?.completedItems || '-' }} / {{ assessment.report?.packageData?.totalItems || '-' }}</p>
                    </div>
                    <div class="rounded-[10px] bg-white p-4 dark:bg-slate-900">
                      <p class="text-xs text-slate-400">报告模块</p>
                      <p class="mt-1 text-sm font-black text-slate-900 dark:text-white">{{ packageSections(assessment).length }} 项</p>
                    </div>
                  </div>

                  <div class="mt-4 rounded-[10px] bg-white p-4 dark:bg-slate-900">
                    <p class="text-xs font-bold text-slate-400">综合结论</p>
                    <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                      {{ assessment.report?.overall?.doctorConclusion || assessment.report?.overall?.summary || assessment.report?.advice || '任务报告已生成。' }}
                    </p>
                  </div>

                  <div class="mt-4 space-y-3">
                    <div v-for="section in packageSections(assessment)" :key="section.type" class="rounded-[10px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <div class="flex flex-wrap items-center gap-2">
                            <p class="font-bold text-slate-900 dark:text-white">{{ section.title || moduleTitle(section.type) }}</p>
                            <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', warningClass(section.riskLevel)]">{{ section.label || warningText(section.riskLevel) }}</span>
                          </div>
                          <p class="mt-1 text-sm leading-6 text-slate-500">{{ section.summary }}</p>
                        </div>
                        <div class="rounded-[8px] bg-slate-50 px-3 py-2 text-right dark:bg-slate-950">
                          <p class="text-[10px] text-slate-400">模块分</p>
                          <p class="text-lg font-black text-slate-900 dark:text-white">{{ section.score ?? 0 }}</p>
                        </div>
                      </div>

                      <div class="mt-3 grid gap-3">
                        <div v-for="(item, index) in section.items || []" :key="`${section.type}-${index}`" class="rounded-[8px] bg-slate-50 p-3 dark:bg-slate-950">
                          <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                            <div>
                              <p class="text-sm font-bold text-slate-900 dark:text-white">{{ item.title }}</p>
                              <p class="mt-1 text-sm leading-6 text-slate-500">{{ item.summary }}</p>
                            </div>
                            <div class="flex items-center gap-2">
                              <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', warningClass(item.riskLevel)]">{{ item.label || warningText(item.riskLevel) }}</span>
                              <span class="text-sm font-black text-slate-800 dark:text-slate-200">{{ item.score ?? 0 }}分</span>
                            </div>
                          </div>
                          <div v-if="asTextList(item.keyFindings).length" class="mt-3">
                            <p class="text-[10px] font-bold text-slate-400">关键结果</p>
                            <p class="mt-1 text-xs leading-6 text-slate-500">{{ asTextList(item.keyFindings).join('；') }}</p>
                          </div>
                          <div v-if="metricEntries(item.metrics).length" class="mt-3 flex flex-wrap gap-2">
                            <span v-for="[key, value] in metricEntries(item.metrics)" :key="key" class="rounded-[8px] bg-white px-2 py-1 text-[10px] font-semibold text-slate-500 dark:bg-slate-900">
                              {{ key }}：{{ value }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activePatientTab === 'scale'" class="space-y-4">
              <div v-if="scaleAssessments.length === 0" class="py-12 text-center text-slate-500">
                <FileText class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无量表评估记录
              </div>

              <div v-for="assessment in scaleAssessments" :key="assessment.id" class="overflow-hidden rounded-[8px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                <button
                  data-testid="patient-scale-report-toggle"
                  class="flex w-full items-center justify-between p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
                  type="button"
                  @click="togglePanel(`scale-${assessment.id}`)"
                >
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 items-center justify-center rounded-[8px] bg-blue-100 text-blue-600">
                      <FileText class="h-4 w-4" />
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">
                          {{ assessment.assessment_type === 'fusion_report' ? 'AI多模态报告' : assessment.assessment_type || 'PHQ-9量表评估' }}
                        </span>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', riskBadgeClass(assessment.risk_level)]">
                          {{ riskText(assessment.risk_level) }}
                        </span>
                      </div>
                      <p class="mt-1 text-xs text-slate-400">{{ new Date(assessment.created_at).toLocaleString('zh-CN') }}</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <div class="text-right">
                      <div class="text-xl font-black text-slate-800 dark:text-slate-200">{{ getScaleData(assessment)?.score ?? getScaleData(assessment)?.phq9_score ?? assessment.score ?? 0 }}</div>
                      <div class="text-[10px] text-slate-400">/ 27分</div>
                    </div>
                    <ChevronUp v-if="expandedPanels[`scale-${assessment.id}`]" class="h-4 w-4 text-slate-400" />
                    <ChevronDown v-else class="h-4 w-4 text-slate-400" />
                  </div>
                </button>

                <div
                  v-if="expandedPanels[`scale-${assessment.id}`]"
                  data-testid="patient-scale-report-detail"
                  class="border-t border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                >
                  <div class="grid gap-4 md:grid-cols-2">
                    <div class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-blue-500" />
                        风险等级分布
                      </h5>
                      <div class="space-y-2">
                        <div
                          v-for="item in [
                            { name: '无抑郁', min: 0, max: 4, tone: 'bg-emerald-500' },
                            { name: '轻度', min: 5, max: 9, tone: 'bg-blue-500' },
                            { name: '中度', min: 10, max: 14, tone: 'bg-amber-500' },
                            { name: '中重度', min: 15, max: 19, tone: 'bg-orange-500' },
                            { name: '重度', min: 20, max: 27, tone: 'bg-rose-500' },
                          ]"
                          :key="item.name"
                        >
                          <div class="mb-1 flex items-center justify-between text-xs text-slate-500">
                            <span>{{ item.name }}</span>
                            <span>{{ item.min }}-{{ item.max }}分</span>
                          </div>
                          <div class="h-3 rounded-full bg-slate-100 dark:bg-slate-800">
                            <div
                              :class="['h-full rounded-full', item.tone]"
                              :style="{
                                width:
                                  (getScaleData(assessment)?.score ?? getScaleData(assessment)?.phq9_score ?? assessment.score ?? 0) >= item.min &&
                                  (getScaleData(assessment)?.score ?? getScaleData(assessment)?.phq9_score ?? assessment.score ?? 0) <= item.max
                                    ? '100%'
                                    : '18%',
                                opacity:
                                  (getScaleData(assessment)?.score ?? getScaleData(assessment)?.phq9_score ?? assessment.score ?? 0) >= item.min &&
                                  (getScaleData(assessment)?.score ?? getScaleData(assessment)?.phq9_score ?? assessment.score ?? 0) <= item.max
                                    ? '1'
                                    : '0.25',
                              }"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div v-if="(getScaleData(assessment)?.dimensionScores || []).length > 0" class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-blue-500" />
                        各维度得分详情
                      </h5>
                      <div class="grid grid-cols-3 gap-2">
                        <div
                          v-for="(dimension, index) in getScaleData(assessment)?.dimensionScores || []"
                          :key="index"
                          class="rounded-[8px] bg-slate-50 p-2.5 dark:bg-slate-950"
                        >
                          <div class="mb-1 text-[10px] text-slate-500">{{ dimension.label }}</div>
                          <div class="flex items-baseline gap-1">
                            <span class="text-base font-bold text-slate-800 dark:text-slate-200">{{ dimension.score }}</span>
                            <span class="text-[10px] text-slate-400">/ {{ dimension.max ?? 3 }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="assessment.report?.content" class="mt-4 rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                    <h5 class="mb-2 text-xs font-bold text-slate-600">评估结论</h5>
                    <p class="text-sm leading-7 text-slate-600 dark:text-slate-300">{{ assessment.report.content }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activePatientTab === 'voice'" class="space-y-4">
              <div v-if="voiceAssessments.length === 0" class="py-12 text-center text-slate-500">
                <Mic class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无语音情绪分析记录
              </div>

              <div v-for="assessment in voiceAssessments" :key="assessment.id" class="overflow-hidden rounded-[8px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                <button
                  data-testid="patient-voice-report-toggle"
                  class="flex w-full items-center justify-between p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
                  type="button"
                  @click="togglePanel(`voice-${assessment.id}`)"
                >
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 items-center justify-center rounded-[8px] bg-violet-100 text-violet-600">
                      <Mic class="h-4 w-4" />
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">语音情绪分析</span>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', (getVoiceData(assessment)?.score ?? 0) > 60 ? 'bg-orange-500 text-white' : 'bg-emerald-500 text-white']">
                          {{ (getVoiceData(assessment)?.score ?? 0) > 60 ? '情绪波动' : '情绪平稳' }}
                        </span>
                      </div>
                      <p class="mt-1 text-xs text-slate-400">{{ new Date(assessment.created_at).toLocaleString('zh-CN') }}</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <div class="text-right">
                      <div class="text-xl font-black text-slate-800 dark:text-slate-200">{{ getVoiceData(assessment)?.score ?? 0 }}</div>
                      <div class="text-[10px] text-slate-400">/ 100</div>
                    </div>
                    <ChevronUp v-if="expandedPanels[`voice-${assessment.id}`]" class="h-4 w-4 text-slate-400" />
                    <ChevronDown v-else class="h-4 w-4 text-slate-400" />
                  </div>
                </button>

                <div
                  v-if="expandedPanels[`voice-${assessment.id}`]"
                  data-testid="patient-voice-report-detail"
                  class="border-t border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                >
                  <div class="grid gap-4 md:grid-cols-2">
                    <div class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-violet-500" />
                        声学特征指标
                      </h5>
                      <div class="grid grid-cols-2 gap-3">
                        <div
                          v-for="feature in [
                            { label: '语速', value: getVoiceData(assessment)?.speech_rate ?? 142, unit: '词/分', status: '偏慢', tone: 'text-amber-500' },
                            { label: '音调变化', value: getVoiceData(assessment)?.pitch_variation ?? 68, unit: '%', status: '正常', tone: 'text-emerald-500' },
                            { label: '音量稳定性', value: getVoiceData(assessment)?.volume_stability ?? 75, unit: '%', status: '良好', tone: 'text-emerald-500' },
                            { label: '停顿频率', value: getVoiceData(assessment)?.pause_frequency ?? 12, unit: '次/分', status: '偏高', tone: 'text-amber-500' },
                          ]"
                          :key="feature.label"
                          class="rounded-[8px] bg-slate-50 p-3 dark:bg-slate-950"
                        >
                          <div class="mb-1 flex items-start justify-between gap-2">
                            <span class="text-xs text-slate-500">{{ feature.label }}</span>
                            <span :class="['text-xs font-medium', feature.tone]">{{ feature.status }}</span>
                          </div>
                          <div class="flex items-baseline gap-1">
                            <span class="text-xl font-bold text-slate-800 dark:text-slate-200">{{ feature.value }}</span>
                            <span class="text-[10px] text-slate-400">{{ feature.unit }}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-violet-500" />
                        6维语音情绪
                      </h5>
                      <div class="space-y-2.5">
                        <div
                          v-for="emotion in [
                            { label: '平静', value: Math.round((getVoiceData(assessment)?.emotions?.calm ?? 0.45) * 100), tone: 'bg-slate-500' },
                            { label: '开心', value: Math.round((getVoiceData(assessment)?.emotions?.happy ?? 0.15) * 100), tone: 'bg-amber-400' },
                            { label: '悲伤', value: Math.round((getVoiceData(assessment)?.emotions?.sad ?? 0.20) * 100), tone: 'bg-blue-500' },
                            { label: '愤怒', value: Math.round((getVoiceData(assessment)?.emotions?.angry ?? 0.08) * 100), tone: 'bg-rose-500' },
                            { label: '恐惧', value: Math.round((getVoiceData(assessment)?.emotions?.fear ?? 0.07) * 100), tone: 'bg-purple-500' },
                            { label: '惊讶', value: Math.round((getVoiceData(assessment)?.emotions?.surprise ?? 0.05) * 100), tone: 'bg-cyan-500' },
                          ]"
                          :key="emotion.label"
                          class="flex items-center gap-2.5"
                        >
                          <span class="w-10 text-xs text-slate-600 dark:text-slate-300">{{ emotion.label }}</span>
                          <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                            <div :class="['h-full rounded-full', emotion.tone]" :style="{ width: `${emotion.value}%` }" />
                          </div>
                          <span class="w-10 text-right text-xs font-bold text-slate-700 dark:text-slate-200">{{ emotion.value }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="getVoiceData(assessment)?.analysis" class="mt-4 rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                    <h5 class="mb-2 text-xs font-bold text-slate-600">分析结论</h5>
                    <p class="text-sm leading-7 text-slate-600 dark:text-slate-300">{{ getVoiceData(assessment)?.analysis }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activePatientTab === 'expression'" class="space-y-4">
              <div v-if="expressionAssessments.length === 0" class="py-12 text-center text-slate-500">
                <Video class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无表情识别分析记录
              </div>

              <div v-for="assessment in expressionAssessments" :key="assessment.id" class="overflow-hidden rounded-[8px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                <button
                  data-testid="patient-expression-report-toggle"
                  class="flex w-full items-center justify-between p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
                  type="button"
                  @click="togglePanel(`expression-${assessment.id}`)"
                >
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 items-center justify-center rounded-[8px] bg-cyan-100 text-cyan-600">
                      <Video class="h-4 w-4" />
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">表情识别分析</span>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-semibold', (getExpressionData(assessment)?.depression_risk_score ?? 0) > 60 ? 'bg-rose-500 text-white' : 'bg-emerald-500 text-white']">
                          {{ (getExpressionData(assessment)?.depression_risk_score ?? 0) > 60 ? '风险较高' : '风险较低' }}
                        </span>
                      </div>
                      <p class="mt-1 text-xs text-slate-400">{{ new Date(assessment.created_at).toLocaleString('zh-CN') }}</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <div class="text-right">
                      <div class="text-xl font-black text-slate-800 dark:text-slate-200">{{ getExpressionData(assessment)?.depression_risk_score ?? 0 }}</div>
                      <div class="text-[10px] text-slate-400">/ 100</div>
                    </div>
                    <ChevronUp v-if="expandedPanels[`expression-${assessment.id}`]" class="h-4 w-4 text-slate-400" />
                    <ChevronDown v-else class="h-4 w-4 text-slate-400" />
                  </div>
                </button>

                <div
                  v-if="expandedPanels[`expression-${assessment.id}`]"
                  data-testid="patient-expression-report-detail"
                  class="border-t border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                >
                  <div class="grid gap-4 md:grid-cols-2">
                    <div
                      v-if="Object.keys(getExpressionData(assessment)?.micro_features || {}).length > 0"
                      class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
                    >
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-cyan-500" />
                        微表情特征分析
                      </h5>
                      <div class="space-y-2.5">
                        <div
                          v-for="(value, key) in getExpressionData(assessment)?.micro_features || {}"
                          :key="key"
                          class="rounded-[8px] bg-slate-50 p-3 dark:bg-slate-950"
                        >
                          <div class="text-[10px] text-slate-500">{{ key }}</div>
                          <div class="mt-1 text-sm font-medium text-slate-700 dark:text-slate-200">{{ value }}</div>
                        </div>
                      </div>
                    </div>

                    <div class="rounded-[8px] border border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                      <h5 class="mb-3 flex items-center gap-1.5 text-xs font-bold text-slate-600">
                        <Activity class="h-3.5 w-3.5 text-cyan-500" />
                        面部表情分布
                      </h5>
                      <div class="space-y-2.5">
                        <div
                          v-for="emotion in [
                            { label: '中性', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.neutral ?? 0.4) || 0) * 100), tone: 'bg-slate-400' },
                            { label: '高兴', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.happy ?? 0.15) || 0) * 100), tone: 'bg-amber-400' },
                            { label: '悲伤', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.sad ?? 0.25) || 0) * 100), tone: 'bg-blue-500' },
                            { label: '愤怒', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.angry ?? 0.05) || 0) * 100), tone: 'bg-rose-500' },
                            { label: '惊讶', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.surprised ?? 0.05) || 0) * 100), tone: 'bg-cyan-500' },
                            { label: '恐惧', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.fearful ?? 0.05) || 0) * 100), tone: 'bg-purple-500' },
                            { label: '厌恶', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.disgusted ?? 0.02) || 0) * 100), tone: 'bg-emerald-500' },
                            { label: '轻蔑', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.contempt ?? 0.02) || 0) * 100), tone: 'bg-orange-400' },
                            { label: '痛苦', value: Math.round(((getExpressionData(assessment)?.facial_expressions?.pain ?? 0.01) || 0) * 100), tone: 'bg-red-600' },
                          ]"
                          :key="emotion.label"
                          class="flex items-center gap-2.5"
                        >
                          <span class="w-10 text-xs text-slate-600 dark:text-slate-300">{{ emotion.label }}</span>
                          <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                            <div :class="['h-full rounded-full', emotion.tone]" :style="{ width: `${emotion.value}%` }" />
                          </div>
                          <span class="w-10 text-right text-xs font-bold text-slate-700 dark:text-slate-200">{{ emotion.value }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activePatientTab === 'intervention'" class="space-y-4">
              <div v-if="interventionPlans.length === 0" class="py-12 text-center text-slate-500">
                <HeartPulse class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无干预计划
              </div>
              <div v-for="plan in interventionPlans" :key="plan.id" class="rounded-[12px] border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <h4 class="font-black text-slate-900 dark:text-white">{{ plan.batch_title }}</h4>
                      <span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">{{ plan.status }}</span>
                      <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-500 dark:bg-slate-800">{{ plan.risk_level || 'manual' }}</span>
                    </div>
                    <p class="mt-2 text-sm leading-6 text-slate-500">{{ plan.batch_description || '干预计划已发布。' }}</p>
                    <p class="mt-2 text-xs text-slate-400">{{ plan.start_date }} 至 {{ plan.end_date }}</p>
                  </div>
                  <div class="grid grid-cols-3 gap-2 text-center text-xs">
                    <span class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950">完成天数<br><b>{{ plan.completed_days || 0 }}/{{ plan.duration_days || 0 }}</b></span>
                    <span class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950">完成次数<br><b>{{ plan.total_completed_count || 0 }}</b></span>
                    <span class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950">项目数<br><b>{{ plan.items?.length || 0 }}</b></span>
                  </div>
                </div>
                <div class="mt-4 flex flex-wrap gap-2">
                  <span v-for="item in plan.items || []" :key="item.id" class="rounded-full bg-slate-50 px-3 py-1 text-xs font-bold text-slate-500 dark:bg-slate-950">
                    {{ item.title }}
                  </span>
                </div>
                <div v-if="plan.summaries?.length" class="mt-4 grid gap-2 md:grid-cols-2">
                  <div v-for="summary in plan.summaries" :key="summary.id" class="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-100">
                    <b>{{ summary.summary_date }}</b> · {{ summary.completed_count }}/{{ summary.required_count }}
                    <p class="mt-1 leading-5">{{ summary.summary_text }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="space-y-4">
              <div v-if="conversationAssessments.length === 0" class="py-12 text-center text-slate-500">
                <MessageSquare class="mx-auto mb-3 h-12 w-12 opacity-30" />
                暂无量表对话记录
              </div>

              <div v-for="assessment in conversationAssessments" :key="assessment.id" class="overflow-hidden rounded-[8px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                <button
                  data-testid="patient-conversation-report-toggle"
                  class="flex w-full items-center justify-between p-4 text-left transition hover:bg-slate-50 dark:hover:bg-slate-950"
                  type="button"
                  @click="togglePanel(`conversation-${assessment.id}`)"
                >
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 items-center justify-center rounded-[8px] bg-indigo-100 text-indigo-600">
                      <MessageSquare class="h-4 w-4" />
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold text-slate-900 dark:text-white">
                          {{ assessment.assessment_type === 'fusion_report' ? 'AI多模态评估对话' : '量表评估对话' }}
                        </span>
                        <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                          {{ getConversationHistory(assessment).filter((item: any) => item.role !== 'system').length }} 条消息
                        </span>
                      </div>
                      <p class="mt-1 text-xs text-slate-400">{{ new Date(assessment.created_at).toLocaleString('zh-CN') }}</p>
                    </div>
                  </div>
                  <ChevronUp v-if="expandedPanels[`conversation-${assessment.id}`]" class="h-4 w-4 text-slate-400" />
                  <ChevronDown v-else class="h-4 w-4 text-slate-400" />
                </button>

                <div
                  v-if="expandedPanels[`conversation-${assessment.id}`]"
                  data-testid="patient-conversation-report-detail"
                  class="border-t border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-950/40"
                >
                  <div class="space-y-3">
                    <div
                      v-for="(message, index) in getConversationHistory(assessment).filter((item: any) => item.role !== 'system')"
                      :key="index"
                      :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']"
                    >
                      <div
                        :class="[
                          'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm',
                          message.role === 'user'
                            ? 'rounded-br-none bg-primary text-white'
                            : 'rounded-bl-none border border-slate-100 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200',
                        ]"
                      >
                        <div v-if="message.role === 'assistant'" class="mb-1.5 flex items-center gap-1.5">
                          <Brain class="h-3 w-3 text-indigo-500" />
                          <span class="text-[10px] font-semibold text-indigo-500">AI评估助手</span>
                        </div>
                        <p class="whitespace-pre-wrap break-words">{{ formatConversationMessage(message) }}</p>
                      </div>
                    </div>
                  </div>
                  <div class="px-1 pt-3 text-center text-[10px] text-slate-400">
                    共 {{ getConversationHistory(assessment).filter((item: any) => item.role !== 'system').length }} 条对话记录
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div
      v-if="codeManagerOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 py-6"
      @click.self="codeManagerOpen = false"
    >
      <div class="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-[8px] bg-white p-6 shadow-xl dark:bg-slate-900">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-xl font-bold text-slate-900 dark:text-white">验证码管理</h3>
            <p class="mt-1 text-sm text-slate-500">管理员端注册验证码管理。默认验证码“2026”永久有效，其他验证码仅可使用一次。</p>
          </div>
          <button class="rounded-[8px] border border-slate-200 px-3 py-2 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-300" type="button" @click="codeManagerOpen = false">
            关闭
          </button>
        </div>

        <div class="mt-6 space-y-6">
          <div class="rounded-[8px] border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/40">
            <h4 class="font-semibold text-slate-900 dark:text-white">新增验证码</h4>
            <div class="mt-4 grid gap-4">
              <div>
                <label class="mb-2 block text-sm text-slate-500">验证码 *</label>
                <input
                  v-model="codeForm.code"
                  data-testid="verification-code-input"
                  class="w-full rounded-[8px] border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                  placeholder="输入新验证码（字母和数字）"
                />
              </div>
              <div>
                <label class="mb-2 block text-sm text-slate-500">备注</label>
                <input
                  v-model="codeForm.notes"
                  class="w-full rounded-[8px] border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                  placeholder="可选：添加备注信息"
                />
              </div>
              <button
                data-testid="create-verification-code"
                class="inline-flex w-full items-center justify-center gap-2 rounded-[8px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900"
                :disabled="creatingCode || !codeForm.code.trim()"
                type="button"
                @click="createCode"
              >
                <Plus class="h-4 w-4" />
                {{ creatingCode ? '创建中...' : '创建验证码' }}
              </button>
            </div>
          </div>

          <div>
            <h4 class="mb-3 font-semibold text-slate-900 dark:text-white">验证码列表</h4>
            <div v-if="loadingCodes" class="py-8 text-center text-slate-500">加载中...</div>
            <div v-else-if="verificationCodes.length === 0" class="py-8 text-center text-slate-500">暂无验证码</div>
            <div v-else class="space-y-2">
              <div
                v-for="code in verificationCodes"
                :key="code.id"
                class="flex items-center justify-between gap-4 rounded-[8px] border border-slate-200 p-4 dark:border-slate-800"
              >
                <div class="min-w-0 flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-3">
                    <code class="rounded-[8px] bg-primary/10 px-3 py-1 text-lg font-bold text-primary">{{ code.code }}</code>
                    <span v-if="code.is_permanent" class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">永久有效</span>
                    <span v-else-if="code.is_used" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">已使用</span>
                    <span v-else class="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">未使用</span>
                  </div>
                  <p v-if="code.notes" class="mb-1 text-sm text-slate-500">{{ code.notes }}</p>
                  <div class="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span>创建于 {{ new Date(code.created_at).toLocaleString('zh-CN') }}</span>
                    <span v-if="code.used_at">• 使用于 {{ new Date(code.used_at).toLocaleString('zh-CN') }}</span>
                  </div>
                </div>

                <div class="flex items-center gap-2">
                  <button class="flex h-9 w-9 items-center justify-center rounded-[8px] border border-slate-200 text-slate-600 dark:border-slate-700 dark:text-slate-300" type="button" @click="copyCode(code.id, code.code)">
                    <Check v-if="copiedCodeId === code.id" class="h-4 w-4 text-emerald-600" />
                    <Copy v-else class="h-4 w-4" />
                  </button>
                  <button
                    v-if="!code.is_permanent"
                    class="flex h-9 w-9 items-center justify-center rounded-[8px] border border-slate-200 text-slate-600 transition hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600 dark:border-slate-700 dark:text-slate-300"
                    type="button"
                    @click="removeCode(code.id, code.code)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
