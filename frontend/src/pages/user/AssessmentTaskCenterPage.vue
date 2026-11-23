<script setup lang="ts">
import {
  ArrowLeft,
  ArrowRight,
  AlertTriangle,
  AudioLines,
  BarChart3,
  Brain,
  Camera,
  CheckCircle2,
  ClipboardList,
  Film,
  FileText,
  Headphones,
  Loader2,
  MessageCircle,
  NotebookPen,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Video,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import ServiceStatus from '@/components/ui/ServiceStatus.vue'
import {
  getAssessmentTaskPackageReport,
  getMyInterventionTodayTasks,
  getMyAssessmentPublishTaskDetail,
  getMyAssessmentPublishTasks,
  startAssessmentTaskItem,
  submitAssessmentTaskModuleItem,
} from '@/db/api'
import { blobToBase64 } from '@/utils/audio'
import type { AssessmentPublishAssignee, AssessmentPublishItemRecord, AssessmentPublishItemType, InterventionTodayResponse, InterventionTodayTask } from '@/types'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const tasks = ref<AssessmentPublishAssignee[]>([])
const taskDetail = ref<any | null>(null)
const activeItem = ref<AssessmentPublishItemRecord | null>(null)
const reportExpanded = ref(false)
const taskItemsExpanded = ref(true)
const interventionToday = ref<InterventionTodayResponse | null>(null)
const dialogueAnswers = ref(['', ''])
const voiceText = ref('')
const voiceState = ref<'idle' | 'recording' | 'done'>('idle')
const expressionNote = ref('')
const expressionSnapshot = ref('')
const cameraVideo = ref<HTMLVideoElement | null>(null)
let mediaRecorder: MediaRecorder | null = null
let audioStream: MediaStream | null = null
let audioChunks: Blob[] = []
let cameraStream: MediaStream | null = null

const assigneeId = computed(() => (typeof route.params.assigneeId === 'string' ? route.params.assigneeId : ''))
const currentAssigneeId = computed(() => assigneeId.value || taskDetail.value?.id || '')
const items = computed<AssessmentPublishItemRecord[]>(() => taskDetail.value?.items || [])
const interventionTasks = computed(() => interventionToday.value?.tasks || [])
const requiredItems = computed(() => items.value.filter((item) => item.required !== false))
const completedItems = computed(() => requiredItems.value.filter((item) => item.status === 'completed' || item.status === 'unsupported'))
const progress = computed(() => (requiredItems.value.length ? Math.round((completedItems.value.length / requiredItems.value.length) * 100) : 0))
const canOpenItem = (item: AssessmentPublishItemRecord) => item.status === 'pending' || item.status === 'in_progress'
const nextItem = computed(() => requiredItems.value.find((item) => item.status === 'in_progress') || requiredItems.value.find(canOpenItem) || items.value.find(canOpenItem))
const isCompletedTask = computed(() => requiredItems.value.length > 0 && completedItems.value.length === requiredItems.value.length)
const showTaskItems = computed(() => !isCompletedTask.value || taskItemsExpanded.value)
const packageReport = computed(() => taskDetail.value?.package_report || null)
const packageReportBody = computed(() => packageReport.value?.report || null)
const packageReportSections = computed(() => normalizeReportSections(packageReportBody.value))
const packageReportTitle = computed(() =>
  packageReportBody.value?.packageData?.reportTitle ||
  (taskDetail.value?.template_code === 'default_forensic_risk_screening' ? '职务犯罪初筛总报告' : '测评任务报告'),
)

const moduleMeta: Record<AssessmentPublishItemType, { label: string; icon: any; tone: string; description: string }> = {
  scale: { label: '量表测评', icon: ClipboardList, tone: 'bg-blue-50 text-blue-600', description: '标准化问卷，评估风险倾向和心理状态。' },
  neuropsych: { label: '神经心理测验', icon: Brain, tone: 'bg-slate-900 text-white', description: '通过认知实验观察风险决策和抑制控制。' },
  dialogue_scale: { label: '对话式心理健康评估', icon: MessageCircle, tone: 'bg-cyan-50 text-cyan-700', description: '用简短对话记录压力、冲动和情绪线索。' },
  voice: { label: '语音识别', icon: AudioLines, tone: 'bg-amber-50 text-amber-700', description: '采集语音文本，辅助观察表达节奏和情绪波动。' },
  expression: { label: '表情评估', icon: Video, tone: 'bg-emerald-50 text-emerald-700', description: '采集面部状态，辅助观察负性情绪线索。' },
  multimodal_baseline: { label: '多模态基线', icon: Sparkles, tone: 'bg-slate-100 text-slate-500', description: '预留模块。' },
}

const isTaskCompleteList = (taskItems: AssessmentPublishItemRecord[] = []) => {
  const required = taskItems.filter((item) => item.required !== false)
  return required.length > 0 && required.every((item) => item.status === 'completed' || item.status === 'unsupported')
}

const syncTaskItemsExpanded = () => {
  taskItemsExpanded.value = !isTaskCompleteList(taskDetail.value?.items || [])
}

const loadTasks = async () => {
  loading.value = true
  errorMessage.value = ''
  taskDetail.value = null
  try {
    tasks.value = await getMyAssessmentPublishTasks()
    interventionToday.value = await getMyInterventionTodayTasks().catch(() => null)
    const targetId = assigneeId.value || tasks.value.find((item) => ['pending', 'in_progress'].includes(item.status))?.id || tasks.value[0]?.id || ''
    if (targetId) {
      taskDetail.value = await getMyAssessmentPublishTaskDetail(targetId)
      syncTaskItemsExpanded()
    } else {
      taskDetail.value = null
      taskItemsExpanded.value = true
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载测评任务失败'
  } finally {
    loading.value = false
  }
}

const loadInterventions = async () => {
  interventionToday.value = await getMyInterventionTodayTasks().catch(() => null)
}

const refreshDetail = async () => {
  if (!currentAssigneeId.value) return
  taskDetail.value = await getMyAssessmentPublishTaskDetail(currentAssigneeId.value)
  syncTaskItemsExpanded()
}

const itemStatusText = (item: AssessmentPublishItemRecord) => {
  if (item.status === 'completed') return '已完成'
  if (item.status === 'in_progress') return '进行中'
  if (item.status === 'expired') return '已过期'
  if (item.status === 'cancelled') return '已取消'
  if (item.status === 'unsupported') return '暂不支持'
  return '待完成'
}

const normalizeReportSections = (report: any) => {
  if (!report) return []
  if (Array.isArray(report.sections) && report.sections.length) return report.sections
  const legacy = [
    { type: 'scale', data: report.scaleData },
    { type: 'neuropsych', data: report.neuropsychData },
    { type: 'dialogue_scale', data: report.dialogueData },
    { type: 'voice', data: report.voiceData },
    { type: 'expression', data: report.expressionData },
  ]
  return legacy
    .filter((item) => item.data && Object.keys(item.data).length > 0)
    .map((item) => {
      const reports = Array.isArray(item.data.reports) ? item.data.reports : [item.data]
      return {
        type: item.type,
        title: moduleMeta[item.type as AssessmentPublishItemType]?.label || '测评项目',
        score: item.data.score ?? item.data.totalScore ?? 0,
        riskLevel: item.data.riskLevel || item.data.warningLevel || item.data.warning_level || 'none',
        summary: item.data.summary || item.data.overall?.summary || '该模块已完成。',
        items: reports.map((report: any, index: number) => ({
          title: report.surveyTitle || report.testTitle || report.title || `${moduleMeta[item.type as AssessmentPublishItemType]?.label || '测评项目'} ${index + 1}`,
          score: report.score ?? report.totalScore ?? 0,
          riskLevel: report.riskLevel || report.warningLevel || report.warning_level || 'none',
          summary: report.summary || report.conclusion || '该测评已完成。',
          keyFindings: report.keyFindings || [],
          suggestions: report.suggestions || [],
        })),
      }
    })
}

const riskLabel = (risk?: string) => {
  if (risk === 'high') return '高风险'
  if (risk === 'middle' || risk === 'medium') return '中风险'
  if (risk === 'low') return '低风险'
  return '低风险'
}

const riskToneClass = (risk?: string) => {
  if (risk === 'high') return 'bg-rose-100 text-rose-700 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-200'
  if (risk === 'middle' || risk === 'medium') return 'bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-200'
  if (risk === 'low') return 'bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200'
  return 'bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-800 dark:text-slate-200'
}

const reportSectionTone = (type: AssessmentPublishItemType) => {
  if (type === 'scale') return 'border-blue-100 bg-blue-50/60 dark:border-blue-900/50 dark:bg-blue-950/20'
  if (type === 'neuropsych') return 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900'
  if (type === 'dialogue_scale') return 'border-cyan-100 bg-cyan-50/70 dark:border-cyan-900/50 dark:bg-cyan-950/20'
  if (type === 'voice') return 'border-amber-100 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20'
  if (type === 'expression') return 'border-emerald-100 bg-emerald-50/70 dark:border-emerald-900/50 dark:bg-emerald-950/20'
  return 'border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-900'
}

const moduleMetaFor = (type: AssessmentPublishItemType) =>
  moduleMeta[type] || { label: '测评项目', icon: FileText, tone: 'bg-slate-100 text-slate-500', description: '测评项目已完成。' }

const textList = (value: any) => Array.isArray(value) ? value.filter(Boolean).map(String) : []

const metricEntries = (metrics: any) =>
  Object.entries(metrics || {})
    .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '')
    .slice(0, 4)

const dateText = (value?: string) => {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN')
}

const interventionMeta = (task: InterventionTodayTask) => {
  if (task.item_type === 'mood') return { label: '心情', icon: NotebookPen, tone: 'bg-amber-50 text-amber-700', duration: '保存日记后完成' }
  if (task.item_type === 'meditation') return { label: '冥想', icon: Headphones, tone: 'bg-cyan-50 text-cyan-700', duration: `${task.duration_sec || 10} 秒后可完成` }
  if (task.item_type === 'knowledge') return { label: task.subtype === 'video' ? '视频' : '文章', icon: task.subtype === 'video' ? Film : FileText, tone: 'bg-emerald-50 text-emerald-700', duration: `${task.duration_sec || 10} 秒后可完成` }
  if (task.item_type === 'game') return { label: '游戏', icon: Film, tone: 'bg-orange-50 text-orange-700', duration: `${task.duration_sec || 10} 秒后可完成` }
  return { label: '脑机', icon: Brain, tone: 'bg-slate-900 text-white', duration: `${task.duration_sec || 10} 秒后可完成` }
}

const interventionStatusText = (status: string) => {
  if (status === 'completed') return '已完成'
  if (status === 'in_progress') return '进行中'
  if (status === 'expired') return '已过期'
  return '待完成'
}

const openInterventionTask = async (task: InterventionTodayTask) => {
  if (task.status === 'completed') {
    statusMessage.value = '今日已完成，可再次进入练习但不会重复计数'
  }
  await router.push(task.navigation_path || task.route_path || '/healing')
}

const openItem = async (item: AssessmentPublishItemRecord) => {
  errorMessage.value = ''
  const returnTo = `/assessment-tasks/${currentAssigneeId.value}`
  if (item.item_type === 'scale' && item.result_ref_id) {
    await router.push({ path: '/scale-assessment', query: { recordId: item.result_ref_id, returnTo } })
    return
  }
  if (item.item_type === 'neuropsych' && item.result_ref_id) {
    await router.push({ path: `/neuropsych-assessment/records/${item.result_ref_id}`, query: { returnTo } })
    return
  }
  if (['dialogue_scale', 'voice', 'expression'].includes(item.item_type)) {
    await startAssessmentTaskItem(item.id)
    await router.push({ path: '/assessment', query: { assigneeId: currentAssigneeId.value, taskItemId: item.id, returnTo } })
    return
  }
  activeItem.value = item
  dialogueAnswers.value = ['', '']
  voiceText.value = ''
  expressionNote.value = ''
  expressionSnapshot.value = ''
  await startAssessmentTaskItem(item.id)
  await refreshDetail()
}

const enterItem = async (item: AssessmentPublishItemRecord) => {
  if (submitting.value) return
  submitting.value = true
  try {
    await openItem(item)
  } catch (error) {
    activeItem.value = null
    errorMessage.value = error instanceof Error ? error.message : '暂时无法进入该测评，请稍后再试。'
  } finally {
    submitting.value = false
  }
}

const completeDialogue = async () => {
  if (!activeItem.value) return
  const text = dialogueAnswers.value.join('\n').trim()
  if (!text) {
    errorMessage.value = '请先完成对话式评估问题'
    return
  }
  await submitCurrentModule({
    rawData: { answers: dialogueAnswers.value, text },
    metrics: { score: scoreTextRisk(text) },
  })
}

const startVoiceRecording = async () => {
  errorMessage.value = ''
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    mediaRecorder = new MediaRecorder(audioStream)
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data)
    }
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      voiceText.value = `已采集 ${Math.max(1, Math.round(blob.size / 1024))}KB 语音样本`
      voiceState.value = 'done'
      stopAudioStream()
    }
    mediaRecorder.start()
    voiceState.value = 'recording'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '无法访问麦克风，请检查浏览器权限'
  }
}

const stopVoiceRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
}

const completeVoice = async () => {
  if (!activeItem.value) return
  const blob = audioChunks.length ? new Blob(audioChunks, { type: 'audio/webm' }) : null
  const audioBase64 = blob ? await blobToBase64(blob) : ''
  const text = voiceText.value.trim() || '用户完成了语音样本采集'
  await submitCurrentModule({
    rawData: { text, audioCaptured: Boolean(blob), audioBase64: audioBase64 ? audioBase64.slice(0, 80) : '' },
    metrics: { score: scoreTextRisk(text), durationSeconds: blob ? 10 : 0 },
  })
}

const startCamera = async () => {
  errorMessage.value = ''
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = cameraStream
      await cameraVideo.value.play()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '无法访问摄像头，请检查浏览器权限'
  }
}

const captureExpression = () => {
  const video = cameraVideo.value
  if (!video) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const context = canvas.getContext('2d')
  if (!context) return
  context.drawImage(video, 0, 0, canvas.width, canvas.height)
  expressionSnapshot.value = canvas.toDataURL('image/jpeg', 0.72)
  stopCamera()
}

const completeExpression = async () => {
  const note = expressionNote.value.trim()
  await submitCurrentModule({
    rawData: { note, snapshotCaptured: Boolean(expressionSnapshot.value) },
    metrics: { score: scoreTextRisk(note) },
  })
}

const submitCurrentModule = async (payload: Record<string, unknown>) => {
  if (!activeItem.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    await submitAssessmentTaskModuleItem(activeItem.value.id, payload)
    activeItem.value = null
    statusMessage.value = '测评项目已完成'
    await refreshDetail()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提交测评项目失败'
  } finally {
    submitting.value = false
  }
}

const buildReport = async () => {
  if (!currentAssigneeId.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    await getAssessmentTaskPackageReport(currentAssigneeId.value)
    reportExpanded.value = false
    statusMessage.value = '综合报告已生成'
    await refreshDetail()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '综合报告生成失败'
  } finally {
    submitting.value = false
  }
}

const scoreTextRisk = (text: string) => {
  const normalized = text.toLowerCase()
  const highWords = ['控制不了', '伤害', '报复', '极端', '自杀', '冲动', '绝望']
  const middleWords = ['压力', '焦虑', '失眠', '愤怒', '后悔', '害怕']
  if (highWords.some((word) => normalized.includes(word))) return 78
  if (middleWords.some((word) => normalized.includes(word))) return 56
  return 24
}

const stopAudioStream = () => {
  audioStream?.getTracks().forEach((track) => track.stop())
  audioStream = null
}

const stopCamera = () => {
  cameraStream?.getTracks().forEach((track) => track.stop())
  cameraStream = null
}

watch(assigneeId, loadTasks, { immediate: true })
onBeforeUnmount(() => {
  stopAudioStream()
  stopCamera()
})
</script>

<template>
  <div class="service-width py-6 sm:py-8">
    <div class="space-y-6">
      <nav aria-label="位置" class="service-muted flex flex-wrap items-center gap-2 text-sm">
        <RouterLink class="service-link inline-flex items-center gap-1" to="/"><ArrowLeft class="h-4 w-4" aria-hidden="true" />我的工作台</RouterLink>
        <span aria-hidden="true">/</span><span>测评任务</span>
      </nav>
      <h1 class="text-2xl font-bold sm:text-[30px]">测评任务详情</h1>

      <div v-if="loading" class="service-muted flex items-center gap-2 text-sm" role="status"><Loader2 class="h-5 w-5 animate-spin" aria-hidden="true" />正在加载测评任务…</div>
      <div v-if="errorMessage" class="service-card bg-rose-50 p-4 text-sm font-semibold text-rose-800" role="alert">
        {{ errorMessage }} <button v-if="!taskDetail" class="service-link ml-2" type="button" @click="loadTasks">重试</button>
      </div>
      <div v-if="statusMessage" class="rounded-2xl bg-emerald-50 p-4 text-sm font-bold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-200">{{ statusMessage }}</div>

      <BaseCard v-if="!loading && !taskDetail && !errorMessage" class="service-card">
        <SectionTitle title="暂无待完成测评" description="你目前没有管理员发布或系统分配的测评任务，可从导航进入自由测评。" />
      </BaseCard>

      <template v-if="taskDetail">
        <div class="service-card grid gap-5 border-l-[3px] border-l-[var(--service-red)] p-4 sm:p-5 md:grid-cols-[1fr_220px]" data-testid="task-overview">
          <div class="space-y-2">
            <span class="service-status" :class="isCompletedTask ? 'service-status-done' : ''">{{ isCompletedTask ? '已完成' : taskDetail.status === 'expired' ? '已过期' : taskDetail.status === 'cancelled' ? '已取消' : completedItems.length || items.some(item => item.status === 'in_progress') ? '办理中' : '待办理' }}</span>
            <h2 class="text-lg font-bold sm:text-xl">{{ taskDetail.batch_title || '测评任务' }}</h2>
            <p v-if="taskDetail.end_at" class="service-muted text-sm">截止时间：{{ dateText(taskDetail.end_at) }}</p>
            <button v-if="nextItem" class="service-button" type="button" :disabled="submitting" data-testid="task-continue" @click="enterItem(nextItem)">
              {{ nextItem.status === 'in_progress' || completedItems.length ? '继续测评' : '开始测评' }} <ArrowRight aria-hidden="true" />
            </button>
          </div>
          <div class="self-center space-y-2">
            <p class="flex justify-between gap-3 text-sm"><span class="service-muted">必办进度</span><strong>{{ completedItems.length }} / {{ requiredItems.length }} 项</strong></p>
            <progress class="service-progress block" :value="progress" max="100" aria-label="必办测评进度" />
          </div>
        </div>

        <section aria-labelledby="task-process">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 id="task-process" class="service-sec-title">办理步骤 <span class="service-muted text-sm font-normal">{{ items.length }} 项</span></h2>
            <div class="flex gap-2">
              <button v-if="isCompletedTask" class="service-button service-outline" type="button" :aria-expanded="showTaskItems" @click="taskItemsExpanded = !taskItemsExpanded">{{ showTaskItems ? '收起步骤' : '展开步骤' }}</button>
              <button class="service-button service-outline" type="button" @click="loadTasks"><RefreshCw aria-hidden="true" />刷新</button>
            </div>
          </div>
          <p v-if="items.length === 0" class="service-card service-muted p-5 text-sm">当前任务暂无测评项目。</p>
          <ol v-else-if="showTaskItems" class="grid gap-2">
          <li
            v-for="(item, index) in items"
            :key="item.id"
            class="service-card service-step p-3 sm:px-4"
            :class="nextItem?.id === item.id ? '!border-[#c8878b]' : ''"
            :aria-current="nextItem?.id === item.id ? 'step' : undefined"
            data-testid="task-step"
          >
            <span class="service-muted w-6 shrink-0 text-center text-xs font-semibold tabular-nums">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="service-icon"><component :is="moduleMetaFor(item.item_type).icon" aria-hidden="true" /></span>
            <div class="min-w-0">
              <h3 class="break-words font-semibold" data-testid="task-step-title">{{ item.title || moduleMetaFor(item.item_type).label }}</h3>
              <p class="service-muted mt-1 text-xs">{{ moduleMetaFor(item.item_type).label }} · {{ item.required === false ? '选办' : '必办' }}</p>
            </div>
            <div class="service-step-actions flex flex-wrap items-center gap-2 sm:justify-end">
              <ServiceStatus :tone="item.status === 'completed' ? 'done' : item.status === 'in_progress' ? 'active' : 'idle'">{{ itemStatusText(item) }}</ServiceStatus>
              <button v-if="canOpenItem(item)" class="service-button service-outline" type="button" :disabled="submitting" :aria-label="`${item.status === 'in_progress' ? '继续' : '开始'}${item.title || moduleMetaFor(item.item_type).label}`" @click="enterItem(item)">
                {{ item.status === 'in_progress' ? '继续' : '开始' }} <ArrowRight aria-hidden="true" />
              </button>
            </div>
          </li>
          </ol>
        </section>
      </template>

      <BaseCard v-if="requiredItems.length && completedItems.length === requiredItems.length">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <SectionTitle :title="packageReportTitle" description="该报告只属于当前测评任务，一个任务生成一份；每日 AI多模态报告仍在多模态评估中查看。" />
          <button class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white disabled:opacity-60 dark:bg-white dark:text-slate-900" :disabled="submitting" type="button" @click="buildReport">
            <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
            <FileText v-else class="h-4 w-4" />
            {{ packageReport ? '重新生成任务报告' : '生成任务报告' }}
          </button>
        </div>

        <div v-if="!packageReportBody" class="mt-5 rounded-lg bg-muted p-5">
          <p class="text-sm font-bold text-slate-700 dark:text-slate-200">可以生成最终报告</p>
          <p class="mt-2 text-sm leading-7 text-slate-500">
            报告会汇总量表、神经心理、对话、语音和表情结果。高风险提示会同步进入管理员端预警。
          </p>
        </div>

        <div v-else class="mt-5 overflow-hidden rounded-[28px] border border-cyan-100 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <div class="service-panel-heading p-5">
            <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span :class="['inline-flex items-center rounded-full px-3 py-1 text-xs font-black ring-1', riskToneClass(packageReportBody.overall?.riskLevel)]">
                    {{ packageReportBody.overall?.label || riskLabel(packageReportBody.overall?.riskLevel) }}
                  </span>
                  <span class="inline-flex items-center gap-1 rounded-full bg-white/80 px-3 py-1 text-xs font-bold text-slate-500 ring-1 ring-cyan-100 dark:bg-slate-900/70 dark:ring-slate-800">
                    <CheckCircle2 class="h-3.5 w-3.5" />
                    已同步管理员端
                  </span>
                </div>
                <h3 class="mt-4 text-2xl font-black text-slate-900 dark:text-white">{{ packageReportBody.packageData?.title || taskDetail?.batch_title }}</h3>
                <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">
                  {{ packageReportBody.overall?.summary || '测评任务报告已生成。' }}
                </p>
                <button
                  class="mt-4 inline-flex items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-bold text-white dark:bg-white dark:text-slate-900"
                  type="button"
                  @click="reportExpanded = !reportExpanded"
                >
                  {{ reportExpanded ? '收起完整报告' : '查看完整报告' }}
                </button>
              </div>
              <div class="rounded-3xl bg-white/85 p-4 text-center shadow-sm ring-1 ring-cyan-100 dark:bg-slate-900/75 dark:ring-slate-800">
                <p class="text-xs font-bold text-slate-400">综合分</p>
                <p class="mt-1 text-4xl font-black text-slate-900 dark:text-white">{{ packageReportBody.overall?.score ?? packageReport?.score ?? 0 }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ dateText(packageReportBody.packageData?.generatedAt || packageReport?.updated_at) }}</p>
              </div>
            </div>
            <div class="mt-5 grid gap-3 md:grid-cols-3">
              <div class="rounded-2xl bg-white/80 p-4 ring-1 ring-cyan-100 dark:bg-slate-900/70 dark:ring-slate-800">
                <p class="text-xs font-bold text-slate-400">完成项目</p>
                <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ packageReportBody.packageData?.completedItems || completedItems.length }} / {{ packageReportBody.packageData?.totalItems || requiredItems.length }}</p>
              </div>
              <div class="rounded-2xl bg-white/80 p-4 ring-1 ring-cyan-100 dark:bg-slate-900/70 dark:ring-slate-800">
                <p class="text-xs font-bold text-slate-400">报告模块</p>
                <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ packageReportSections.length }} 项</p>
              </div>
              <div class="rounded-2xl bg-white/80 p-4 ring-1 ring-cyan-100 dark:bg-slate-900/70 dark:ring-slate-800">
                <p class="text-xs font-bold text-slate-400">报告类型</p>
                <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ packageReportBody.packageData?.taskType === 'initial_screening' ? '初筛任务' : '测评任务' }}</p>
              </div>
            </div>
          </div>

          <div v-if="reportExpanded" class="space-y-5 p-5">
            <div class="rounded-[24px] border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-start gap-3">
                <div class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-white text-cyan-700 dark:bg-slate-950 dark:text-cyan-300">
                  <ShieldCheck class="h-5 w-5" />
                </div>
                <div>
                  <p class="text-sm font-black text-slate-900 dark:text-white">给你的结果说明</p>
                  <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                    {{ packageReportBody.overall?.patientConclusion || packageReportBody.advice || '本报告用于筛查和随访参考，不等同于临床诊断。' }}
                  </p>
                </div>
              </div>
            </div>

            <article
              v-for="section in packageReportSections"
              :key="section.type"
              :class="['rounded-[24px] border p-4', reportSectionTone(section.type)]"
            >
              <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div class="flex gap-3">
                  <div :class="['grid h-11 w-11 shrink-0 place-items-center rounded-2xl', moduleMetaFor(section.type).tone]">
                    <component :is="moduleMetaFor(section.type).icon" class="h-5 w-5" />
                  </div>
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <h4 class="text-base font-black text-slate-900 dark:text-white">{{ section.title }}</h4>
                      <span :class="['rounded-full px-2.5 py-1 text-xs font-bold ring-1', riskToneClass(section.riskLevel)]">{{ section.label || riskLabel(section.riskLevel) }}</span>
                    </div>
                    <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ section.summary }}</p>
                  </div>
                </div>
                <div class="rounded-2xl bg-white/85 px-4 py-3 text-center shadow-sm dark:bg-slate-950/70">
                  <p class="text-[10px] font-bold text-slate-400">模块分</p>
                  <p class="text-2xl font-black text-slate-900 dark:text-white">{{ section.score ?? 0 }}</p>
                </div>
              </div>

              <div class="mt-4 grid gap-3">
                <div v-for="(item, index) in section.items || []" :key="`${section.type}-${index}`" class="rounded-[20px] bg-white p-4 ring-1 ring-slate-100 dark:bg-slate-950 dark:ring-slate-800">
                  <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div class="flex flex-wrap items-center gap-2">
                        <p class="font-black text-slate-900 dark:text-white">{{ item.title }}</p>
                        <span :class="['rounded-full px-2 py-0.5 text-[10px] font-bold ring-1', riskToneClass(item.riskLevel)]">{{ item.label || riskLabel(item.riskLevel) }}</span>
                      </div>
                      <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">{{ item.summary }}</p>
                    </div>
                    <div class="flex items-center gap-2 rounded-2xl bg-slate-50 px-3 py-2 dark:bg-slate-900">
                      <BarChart3 class="h-4 w-4 text-slate-400" />
                      <span class="text-sm font-black text-slate-900 dark:text-white">{{ item.score ?? 0 }}</span>
                    </div>
                  </div>

                  <div v-if="textList(item.keyFindings).length" class="mt-4 rounded-2xl bg-slate-50 p-3 dark:bg-slate-900">
                    <p class="text-xs font-black text-slate-500">关键结果</p>
                    <ul class="mt-2 space-y-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      <li v-for="finding in textList(item.keyFindings)" :key="finding">· {{ finding }}</li>
                    </ul>
                  </div>

                  <div v-if="textList(item.suggestions).length" class="mt-3 rounded-2xl bg-emerald-50 p-3 dark:bg-emerald-950/20">
                    <p class="text-xs font-black text-emerald-700 dark:text-emerald-200">建议</p>
                    <ul class="mt-2 space-y-1 text-sm leading-6 text-emerald-800 dark:text-emerald-100">
                      <li v-for="suggestion in textList(item.suggestions)" :key="suggestion">· {{ suggestion }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </article>

            <div class="rounded-[24px] border border-amber-100 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
              <div class="flex gap-3">
                <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-200" />
                <p class="text-sm leading-7 text-amber-800 dark:text-amber-100">
                  {{ packageReportBody.advice || '报告仅作为筛查和随访参考。如你对结果有疑问，建议联系管理员进行进一步沟通。' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <section aria-label="今日干预" class="border-t border-[var(--service-border)] pt-5">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h2 class="service-sec-title">今日干预</h2>
          <button class="service-button service-outline" type="button" @click="loadInterventions">
            <RefreshCw aria-hidden="true" />
            刷新干预
          </button>
        </div>
        <div v-if="!interventionTasks.length" class="mt-5 rounded-[24px] bg-slate-50 p-6 text-sm leading-7 text-slate-500 dark:bg-slate-900">
          今日暂无管理员发布的干预任务。你仍可进入“疗愈”进行自由练习。
        </div>
        <div v-else class="mt-5 grid gap-3 md:grid-cols-2">
          <article v-for="task in interventionTasks" :key="task.id" class="service-card p-4">
            <div class="flex items-center gap-3">
              <div class="service-icon">
                <component :is="interventionMeta(task).icon" aria-hidden="true" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <p class="truncate text-sm font-black text-slate-900 dark:text-white">{{ task.title }}</p>
                  <span class="rounded-full px-2 py-0.5 text-[10px] font-bold" :class="task.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-white text-slate-500 dark:bg-slate-800'">
                    {{ interventionStatusText(task.status) }}
                  </span>
                </div>
                <p class="mt-1 text-xs text-slate-500">{{ interventionMeta(task).label }} · {{ interventionMeta(task).duration }}</p>
                <p class="mt-1 truncate text-[11px] text-slate-400">{{ task.batch_title }}</p>
              </div>
              <button class="service-button service-outline shrink-0" type="button" @click="openInterventionTask(task)">
                {{ task.status === 'completed' ? '再练习' : '去完成' }}
              </button>
            </div>
          </article>
        </div>
        <div v-if="interventionToday" class="service-card mt-5 p-4 text-sm">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p class="font-black">今日干预进度：{{ interventionToday.summary.completed }} / {{ interventionToday.summary.total }}</p>
            </div>
            <button class="service-button service-outline shrink-0" type="button" @click="router.push('/profile/healing-plan')">
              查看疗愈计划
            </button>
          </div>
        </div>
      </section>
    </div>

    <div v-if="activeItem" class="fixed inset-0 z-[80] overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm">
      <section class="mx-auto my-6 max-w-2xl overflow-hidden rounded-[28px] bg-white shadow-2xl dark:bg-slate-950">
        <header class="border-b border-slate-100 p-5 dark:border-slate-800">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.12em] text-primary/70">{{ moduleMeta[activeItem.item_type]?.label }}</p>
              <h2 class="mt-1 text-2xl font-black text-slate-900 dark:text-white">{{ activeItem.title }}</h2>
            </div>
            <button class="rounded-xl px-3 py-2 text-sm font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900" type="button" @click="activeItem = null">关闭</button>
          </div>
        </header>

        <div class="space-y-5 p-5">
          <template v-if="activeItem.item_type === 'dialogue_scale'">
            <div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p class="text-sm font-bold text-slate-700 dark:text-slate-200">请用自己的话回答下面两个问题</p>
            </div>
            <textarea v-model="dialogueAnswers[0]" class="min-h-28 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900" placeholder="最近一周，你的压力、冲动或情绪变化如何？" />
            <textarea v-model="dialogueAnswers[1]" class="min-h-28 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900" placeholder="当遇到诱惑、冲突或强烈情绪时，你通常如何控制自己的行为？" />
            <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white" :disabled="submitting" type="button" @click="completeDialogue">
              <Send class="h-4 w-4" />
              完成对话式评估
            </button>
          </template>

          <template v-else-if="activeItem.item_type === 'voice'">
            <div class="rounded-2xl bg-amber-50 p-4 text-sm leading-7 text-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
              请录制一段 10 秒以内语音，或直接输入本次语音转写文本。移动端如无法录音，可以使用文字兜底完成。
            </div>
            <div class="flex flex-wrap gap-3">
              <button class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white" type="button" @click="voiceState === 'recording' ? stopVoiceRecording() : startVoiceRecording()">
                <AudioLines class="h-4 w-4" />
                {{ voiceState === 'recording' ? '停止录音' : '开始录音' }}
              </button>
              <span class="inline-flex items-center rounded-xl bg-slate-100 px-4 py-3 text-sm font-bold text-slate-500 dark:bg-slate-900">{{ voiceState === 'recording' ? '正在录音' : voiceState === 'done' ? '已采集语音' : '等待采集' }}</span>
            </div>
            <textarea v-model="voiceText" class="min-h-28 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900" placeholder="可填写语音转写文本或当下想表达的内容" />
            <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white" :disabled="submitting" type="button" @click="completeVoice">
              <Send class="h-4 w-4" />
              完成语音识别
            </button>
          </template>

          <template v-else-if="activeItem.item_type === 'expression'">
            <div class="overflow-hidden rounded-2xl bg-slate-950 p-4 text-white">
              <video ref="cameraVideo" class="aspect-video w-full rounded-xl bg-black object-cover" playsinline muted />
              <img v-if="expressionSnapshot" :src="expressionSnapshot" alt="表情采集快照" class="mt-3 aspect-video w-full rounded-xl object-cover" />
            </div>
            <div class="flex flex-wrap gap-3">
              <button class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" type="button" @click="startCamera">
                <Camera class="h-4 w-4" />
                打开摄像头
              </button>
              <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700 dark:border-slate-800 dark:text-slate-200" type="button" @click="captureExpression">
                采集快照
              </button>
            </div>
            <textarea v-model="expressionNote" class="min-h-24 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900" placeholder="可补充当前面部状态或情绪感受" />
            <button class="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white" :disabled="submitting" type="button" @click="completeExpression">
              <Send class="h-4 w-4" />
              完成表情评估
            </button>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>
