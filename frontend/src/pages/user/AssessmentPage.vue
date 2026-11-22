<script setup lang="ts">
import {
  Activity,
  AlertCircle,
  BarChart3,
  Brain,
  Calendar,
  Check,
  ChevronLeft,
  Clock,
  ClipboardList,
  Download,
  FileText,
  Heart,
  History,
  Info,
  Lightbulb,
  Mic,
  Maximize,
  Printer,
  RefreshCcw,
  RotateCcw,
  ScanFace,
  Send,
  Shield,
  Smile,
  Stethoscope,
  StopCircle,
  Upload,
  Video,
  X,
} from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useAppState } from '@/composables/useAppState'
import { useAuthSession } from '@/composables/useAuthSession'
import { useMedia } from '@/composables/useMedia'
import {
  chatCompletion,
  getKnowledgeBase,
  getMyAssessmentPublishTasks,
  multimodalAnalysis,
  multimodalFusion,
  speechRecognition,
  submitAssessmentTaskModuleItem,
} from '@/db/api'
import { resolveAvatarSource } from '@/lib/avatar-presets'
import { blobToBase64, convertWebmToWav } from '@/utils/audio'
import { exportElementReport } from '@/utils/report-export'
import type { AssessmentPublishAssignee, AssessmentPublishItemRecord } from '@/types'

type Step = 'scale' | 'voice' | 'expression' | 'report'
type ScaleId = 'PHQ-9' | 'HAMD-17' | 'SDS-20'
type VoiceState = 'idle' | 'recording' | 'analyzing' | 'done'

interface ScaleMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ScaleResult {
  score: number
  phq9_score: number
  raw_score: number
  max_raw_score: number
  riskLevel: 'low' | 'medium' | 'high'
  risk_level: 'low' | 'medium' | 'high'
  scaleTypes: ScaleId[]
  dimensionScores: Array<{ label: string; score: number; max: number }>
  conversationHistory: Array<{ role: string; content: string; timestamp: string }>
}

interface ModuleResult {
  score: number
  label: string
  summary: string
}

interface VoiceReport {
  text: string
  confidence: number
  emotionVector: Record<string, number>
  speechMetrics: {
    speed: string
    tone: string
    pause: string
    energy: string
  }
  indicators: {
    isLowSpeed: boolean
    isHighPitchDrop: boolean
    isLongPause: boolean
  }
  depressionAnalysis: string
}

interface ExpressionAiReport {
  emotion_radar: Record<string, number>
  depression_risk_score: number
  analysis_report: string
  micro_features: {
    brow_furrow: string
    mouth_droop: string
    eye_contact: string
  }
}

const router = useRouter()
const route = useRoute()
const { isMobile } = useMedia()
const { addAssessment, refreshAssessments, state } = useAppState()
const { state: authState } = useAuthSession()
const routeTaskItemId = computed(() => (typeof route.query.taskItemId === 'string' ? route.query.taskItemId : ''))
const routeAssigneeId = computed(() => (typeof route.query.assigneeId === 'string' ? route.query.assigneeId : ''))

const step = ref<Step>('scale')
const selectedScales = ref<ScaleId[]>(['PHQ-9'])
const scaleStarted = ref(false)
const scaleMessages = ref<ScaleMessage[]>([])
const scaleInputText = ref('')
const scaleLoading = ref(false)
const scaleVoiceListening = ref(false)
const scaleVoiceBusy = ref(false)
const scaleQuestionIndex = ref(0)
const scaleTotalQuestions = ref(9)
const scaleQuestionBank = ref<string[]>([])
const scaleResult = ref<ScaleResult | null>(null)
const scaleMessagesEl = ref<HTMLElement | null>(null)
const scaleReportEl = ref<HTMLElement | null>(null)
const scaleHistoryOpen = ref(false)
const scaleHistoryDetailOpen = ref(false)
const scaleHistoryReportOpen = ref(false)
const selectedScaleHistory = ref<HistoryScaleAssessment | null>(null)
const scaleResumeBanner = ref(false)
const scaleEmojiPickerOpen = ref(false)
const scaleTypingMessageIndex = ref<number | null>(null)
const scaleTypingText = ref('')
const scaleInteractionLocked = computed(() => scaleLoading.value || scaleTypingMessageIndex.value !== null)
const scaleReportOpen = ref(false)
const scaleReadCountdown = ref(0)
const scaleCompleted = ref(false)
const voiceCompleted = ref(false)
const expressionCompleted = ref(false)
const report = ref<{
  scale: ModuleResult
  voice: ModuleResult
  expression: ModuleResult
  overall: ModuleResult
} | null>(null)
const activeReport = ref<'scale' | 'voice' | 'expression' | null>(null)
const reportGeneratedAt = ref('')
const reportAdvice = ref('')
const fusionReportEl = ref<HTMLElement | null>(null)
const fusionHistoryOpen = ref(false)
const fusionHistoryLoading = ref(false)
const publishTasks = ref<AssessmentPublishAssignee[]>([])
const taskSyncing = ref(false)
const taskSyncDone = ref(false)

const statusMessage = ref('')
const errorMessage = ref('')
const toastMessage = computed(() => errorMessage.value || statusMessage.value)
const toastTone = computed(() => (errorMessage.value ? 'error' : 'success'))
let toastTimer: ReturnType<typeof setTimeout> | null = null
const doctorAvatarUrl = 'https://www.keaitupian.cn/cjpic/frombd/1/253/56496682/3498759028.jpg'
const userAvatarSource = computed(() => resolveAvatarSource(authState.profile?.avatar_url))
const userInitial = computed(() =>
  (authState.profile?.full_name || authState.profile?.username || authState.user?.email || 'U').charAt(0).toUpperCase(),
)

const scaleCards = [
  {
    id: 'PHQ-9' as const,
    title: 'PHQ-9 健康问卷',
    subtitle: '用于筛查抑郁症状及其严重程度',
    questions: 9,
    duration: '约 5 分钟',
  },
  {
    id: 'HAMD-17' as const,
    title: 'HAMD-17 汉密尔顿量表',
    subtitle: '临床评估抑郁状态的标准量表',
    questions: 17,
    duration: '约 8 分钟',
  },
  {
    id: 'SDS-20' as const,
    title: 'SDS-20 自评量表',
    subtitle: '直观反映抑郁的主观感受',
    questions: 20,
    duration: '约 10 分钟',
  },
]

interface HistoryScaleAssessment {
  id: string
  date: Date
  scaleTypes: ScaleId[]
  riskLevel: 'low' | 'medium' | 'high'
  score: number
  summary: string
  messages: Array<ScaleMessage & { avatar?: string }>
  reportData: {
    score: number
    riskLevel: 'low' | 'medium' | 'high'
    suggestion: string
    dimensionScores?: Array<{ label: string; score: number; max?: number }>
  }
}

interface ScaleSessionDraft {
  version?: string
  userId?: string
  selectedScales: ScaleId[]
  questionIndex: number
  totalQuestions: number
  questionBank: string[]
  messages: Array<{ role: ScaleMessage['role']; content: string; timestamp: string }>
  updatedAt?: string
  completed?: boolean
}

const SCALE_SESSION_VERSION = 'v1'
const SCALE_SESSION_MAX_AGE_DAYS = 7
const legacyScaleSessionKey = 'chuxin.scale-assessment.session'
const currentScaleSessionKey = computed(() =>
  state.currentAccountId
    ? `mindcare_assessment_session_${SCALE_SESSION_VERSION}_${state.currentAccountId}`
    : legacyScaleSessionKey,
)

const historyScaleAssessments: HistoryScaleAssessment[] = [
  {
    id: 'assess-001',
    date: new Date(2024, 0, 15, 14, 30),
    scaleTypes: ['PHQ-9'],
    riskLevel: 'low',
    score: 8,
    summary: '整体心理状态良好，偶尔有轻微焦虑情绪，建议保持规律作息。',
    messages: [
      { role: 'assistant', content: '你好！我是初心助手。接下来我们将进行 PHQ-9 评估。我会以温暖、共情的方式引导你逐步完成。', timestamp: new Date(2024, 0, 15, 14, 30) },
      { role: 'user', content: '好的，我准备好了', timestamp: new Date(2024, 0, 15, 14, 31) },
      { role: 'assistant', content: '【第1题】在过去两周内，你是否经常感到心情低落、沮丧或绝望？', timestamp: new Date(2024, 0, 15, 14, 31) },
      { role: 'user', content: '偶尔会有这样的感觉，大概一周有2-3天吧', timestamp: new Date(2024, 0, 15, 14, 32) },
      { role: 'assistant', content: '感谢你的配合！PHQ-9评估已完成。根据你的回答，你的得分是8分，属于低风险范围。', timestamp: new Date(2024, 0, 15, 14, 41) },
    ],
    reportData: {
      score: 8,
      riskLevel: 'low',
      suggestion: '您的得分反映出心理状态相对健康，请继续保持积极的生活方式。',
    },
  },
  {
    id: 'assess-002',
    date: new Date(2024, 0, 22, 10, 15),
    scaleTypes: ['PHQ-9', 'HAMD-17'],
    riskLevel: 'medium',
    score: 15,
    summary: '存在一定程度的抑郁倾向，建议通过运动、社交等方式调节情绪。',
    messages: [
      { role: 'assistant', content: '你好！今天我们将进行 PHQ-9, HAMD-17 综合评估。这将帮助我们更全面地了解你的心理状态。', timestamp: new Date(2024, 0, 22, 10, 15) },
      { role: 'user', content: '嗯，可以开始', timestamp: new Date(2024, 0, 22, 10, 16) },
      { role: 'assistant', content: '【PHQ-9 第1题】最近两周，你的睡眠质量如何？是否有入睡困难或早醒的情况？', timestamp: new Date(2024, 0, 22, 10, 16) },
      { role: 'user', content: '睡眠确实不太好，经常要一两个小时才能入睡', timestamp: new Date(2024, 0, 22, 10, 17) },
      { role: 'assistant', content: '综合评估已完成，你的得分是15分，属于中度风险。建议通过运动、社交和充足睡眠来调节情绪。', timestamp: new Date(2024, 0, 22, 10, 26) },
    ],
    reportData: {
      score: 15,
      riskLevel: 'medium',
      suggestion: '您的得分反映出存在一定的心理压力，可以通过运动、社交和充足睡眠来调节。',
    },
  },
  {
    id: 'assess-003',
    date: new Date(2024, 1, 5, 16, 45),
    scaleTypes: ['SDS-20'],
    riskLevel: 'low',
    score: 6,
    summary: '心理状态稳定，情绪管理良好，继续保持当前的生活节奏。',
    messages: [
      { role: 'assistant', content: '你好！我们今天将进行 SDS-20 自评量表评估。这个量表能帮助你更直观地了解自己的情绪状态。', timestamp: new Date(2024, 1, 5, 16, 45) },
      { role: 'user', content: '好的，开始吧', timestamp: new Date(2024, 1, 5, 16, 46) },
      { role: 'assistant', content: '【SDS-20 第1题】我感到情绪沮丧，郁闷', timestamp: new Date(2024, 1, 5, 16, 46) },
      { role: 'user', content: '很少有这种感觉', timestamp: new Date(2024, 1, 5, 16, 47) },
      { role: 'assistant', content: '【SDS-20 第2题】我感到早晨心情最好', timestamp: new Date(2024, 1, 5, 16, 47) },
      { role: 'user', content: '是的，早上精神最好', timestamp: new Date(2024, 1, 5, 16, 48) },
      { role: 'assistant', content: '评估进展顺利。根据目前的回答，你的情绪状态很稳定。SDS-20评估已完成，得分6分，属于低风险范围。', timestamp: new Date(2024, 1, 5, 16, 55) },
    ],
    reportData: {
      score: 6,
      riskLevel: 'low',
      suggestion: '您的得分反映出心理状态相对健康，请继续保持积极的生活方式。',
    },
  },
  {
    id: 'assess-004',
    date: new Date(2024, 1, 18, 9, 20),
    scaleTypes: ['PHQ-9'],
    riskLevel: 'high',
    score: 22,
    summary: '检测到明显的抑郁症状，强烈建议及时寻求专业心理咨询或医疗帮助。',
    messages: [
      { role: 'assistant', content: '你好！感谢你选择进行心理评估。我会陪伴你完成整个过程，请放松心情，真实表达你的感受。', timestamp: new Date(2024, 1, 18, 9, 20) },
      { role: 'user', content: '最近状态很不好，想做个评估看看', timestamp: new Date(2024, 1, 18, 9, 21) },
      { role: 'assistant', content: '【第1题】过去两周，你是否经常感到心情低落、沮丧或绝望？', timestamp: new Date(2024, 1, 18, 9, 21) },
      { role: 'user', content: '是的，几乎每天都有这种感觉', timestamp: new Date(2024, 1, 18, 9, 22) },
      { role: 'assistant', content: '【安全预警】检测到您可能存在自杀风险。我们非常关心您的安全。', timestamp: new Date(2024, 1, 18, 9, 29) },
      { role: 'assistant', content: '评估已完成。你的得分是22分，属于高风险范围。我强烈建议你尽快寻求专业心理咨询或医疗帮助。', timestamp: new Date(2024, 1, 18, 9, 32) },
    ],
    reportData: {
      score: 22,
      riskLevel: 'high',
      suggestion: '您的得分反映出显著的抑郁倾向，建议尽快咨询专业管理员进行干预。',
    },
  },
  {
    id: 'assess-005',
    date: new Date(2024, 1, 25, 14, 0),
    scaleTypes: ['HAMD-17', 'SDS-20'],
    riskLevel: 'medium',
    score: 13,
    summary: '情绪波动较大，需要关注压力来源，建议加强自我调节和放松训练。',
    messages: [
      { role: 'assistant', content: '你好！今天我们将进行 HAMD-17, SDS-20 综合评估。这将从不同维度了解你的心理状态。', timestamp: new Date(2024, 1, 25, 14, 0) },
      { role: 'user', content: '好的，麻烦了', timestamp: new Date(2024, 1, 25, 14, 1) },
      { role: 'assistant', content: '【HAMD-17 第1题】抑郁情绪：最近一周你的情绪状态如何？', timestamp: new Date(2024, 1, 25, 14, 1) },
      { role: 'user', content: '情绪起伏比较大，时好时坏', timestamp: new Date(2024, 1, 25, 14, 2) },
      { role: 'assistant', content: '【HAMD-17 第2题】工作兴趣：你对工作的热情如何？', timestamp: new Date(2024, 1, 25, 14, 2) },
      { role: 'user', content: '工作热情不如以前，有时候会拖延', timestamp: new Date(2024, 1, 25, 14, 3) },
      { role: 'assistant', content: '【SDS-20 第1题】我感到情绪沮丧，郁闷', timestamp: new Date(2024, 1, 25, 14, 5) },
      { role: 'user', content: '有时候会有这种感觉', timestamp: new Date(2024, 1, 25, 14, 6) },
      { role: 'assistant', content: '综合评估已完成，你的得分是13分，属于中度风险。情绪波动较大，建议关注压力来源，适当进行放松训练。', timestamp: new Date(2024, 1, 25, 14, 10) },
    ],
    reportData: {
      score: 13,
      riskLevel: 'medium',
      suggestion: '您的得分反映出存在一定的心理压力，可以通过运动、社交和充足睡眠来调节。',
    },
  },
]

const builtinScaleQuestions: Record<ScaleId, string[]> = {
  'PHQ-9': [
    '兴趣减退：做事提不起劲或没有兴趣？',
    '情绪低落：感到忧郁、沮丧或绝望？',
    '睡眠问题：入睡困难、多梦、早醒或睡眠过多？',
    '精力不足：感觉疲倦或没有体力？',
    '食欲改变：食欲不振或暴饮暴食？',
    '自我评价低：觉得自己很失败或让自己/家人失望？',
    '注意力困难：很难集中注意力，例如阅读或看电视？',
    '精神运动改变：行动或说话变慢，或烦躁坐立不安？',
    '自伤/自杀意念：有轻生或自残的念头？',
  ],
  'HAMD-17': [
    '抑郁心境：过去一周大部分时间感到抑郁、悲伤？',
    '罪疚感：对过往或现状有明显内疚或自责？',
    '自杀意念：出现轻生或自伤想法与言语？',
    '入睡困难：卧床后半小时以上不能入睡？',
    '睡眠维持：夜间多次醒来且难以再入睡？',
    '早醒：较平时更早醒且无法再睡？',
    '工作/活动减少：工作效率下降或兴趣显著降低？',
    '精神运动迟滞：动作、言语明显缓慢？',
    '激越：烦躁不安，坐立不宁或来回走动？',
    '焦虑（心理）：紧张、担忧、容易紧张的主观体验？',
    '焦虑（躯体）：心悸、出汗、手抖等躯体症状？',
    '胃肠道症状：食欲下降、恶心或胃部不适？',
    '全身躯体症状：头痛、乏力、身体不适？',
    '性功能症状：性欲减退或相关问题？',
    '疑病倾向：过度担心身体疾病？',
    '体重下降：近期体重较以往明显减少？',
    '洞察力：对自身病情的认识与配合程度如何？',
  ],
  'SDS-20': [
    '心境低落：我觉得心情不好，心里很难过？',
    '早晨状态：我觉得早晨心情最好？',
    '哭泣倾向：我要哭，或者想哭？',
    '睡眠问题：我夜间睡眠不好？',
    '食欲情况：我吃饭跟平时一样多？',
    '人际愉悦：我跟异性接触时，和以往一样感到愉快？',
    '体重变化：我发觉我的体重在下降？',
    '便秘困扰：我有便秘的苦恼？',
    '心率变化：我心跳比平时快？',
    '疲乏感：我无缘无故地感到疲乏？',
    '思维清晰度：我的头脑跟平时一样清楚？',
    '做事难度：我觉得做任何事情都没有困难？',
    '焦虑不安：我觉得不安而平静不下来？',
    '未来期望：我对未来抱有希望？',
    '易激惹：我比平时更容易激怒？',
    '决策能力：我觉得决定什么事很容易？',
    '自我价值：我觉得自己是个有用的人，有人需要我？',
    '生活意义：我的生活很有意义？',
    '自杀意念：我觉得如果我死了，别人会生活得更好？',
    '兴趣保持：我仍然喜爱我平时喜爱的东西？',
  ],
}

const quickScaleResponses = ['是的', '不是', '有时候', '经常', '很少']
const scaleEmojiList = [
  '😊', '😃', '😄', '😁', '😆', '😅', '🤣', '😂',
  '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗',
  '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨',
  '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞',
  '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫',
  '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬',
  '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥',
  '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐',
]
const currentScaleCard = computed(() => scaleCards.find((item) => selectedScales.value.includes(item.id)) ?? scaleCards[0]!)
const scaleScore = computed(() => {
  if (!scaleResult.value) return 0
  return Math.round((scaleResult.value.score / 27) * 100)
})

const voiceRecognizedText = ref('')
const voiceCaptureState = ref<VoiceState>('idle')
const voiceDuration = ref(0)
const voiceAnalysisProgress = ref(0)
const voiceWaveform = ref<number[]>(Array.from({ length: 50 }, () => 8))
const voiceReportOpen = ref(false)
const voiceFileName = ref('')
const voiceReport = ref<VoiceReport | null>(null)
const audioInput = ref<HTMLInputElement | null>(null)
const voiceReportEl = ref<HTMLElement | null>(null)
let scaleVoiceRecorder: MediaRecorder | null = null
let scaleVoiceStream: MediaStream | null = null
let scaleVoiceChunks: Blob[] = []
let scaleSpeechRecognition: any = null
let scaleVoiceBrowserText = ''
let scaleVoiceAsrBusy = false
let scaleVoiceAsrErrorCount = 0
let scaleVoiceStopRequested = false
let scaleTypingTimer: number | null = null
let scaleReadTimer: ReturnType<typeof setInterval> | null = null
let voiceTimer: ReturnType<typeof setInterval> | null = null
let voiceProgressTimer: ReturnType<typeof setInterval> | null = null
let mediaRecorder: MediaRecorder | null = null
let micStream: MediaStream | null = null
let audioChunks: Blob[] = []
let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let waveformFrame = 0

const expressionStatus = ref<'idle' | 'capturing' | 'analyzing' | 'completed'>('idle')
const expressionCameraStarted = ref(false)
const expressionCountdown = ref(5)
const expressionProgress = ref(0)
const expressionFps = ref(0)
const expressionNoFaceCount = ref(0)
const expressionReportOpen = ref(false)
const expressionDominantEmotion = ref('中性')
const expressionConfidence = ref(0.62)
const expressionSignals = ref({ brow: 0.18, mouth: 0.22, blink: 0.34 })
const expressionVideo = ref<HTMLVideoElement | null>(null)
const expressionSnapshot = ref('')
const expressionAiReport = ref<ExpressionAiReport | null>(null)
const expressionFacingMode = ref<'user' | 'environment'>('user')
let expressionTimer: ReturnType<typeof setInterval> | null = null
let expressionProgressTimer: ReturnType<typeof setInterval> | null = null
let expressionStream: MediaStream | null = null
let expressionFpsFrame = 0
let expressionLastFrameAt = 0

const completedCount = computed(() => [scaleCompleted.value, voiceCompleted.value, expressionCompleted.value].filter(Boolean).length)
const allCompleted = computed(() => completedCount.value === 3)
const incompleteMultimodalItems = (task: AssessmentPublishAssignee) =>
  (task.items || [])
    .filter((item) => ['dialogue_scale', 'voice', 'expression'].includes(item.item_type))
    .filter((item) => item.status !== 'completed' && item.status !== 'unsupported')

const activeMultimodalTask = computed(() => {
  if (routeAssigneeId.value) {
    return publishTasks.value.find((task) => task.id === routeAssigneeId.value) || null
  }
  return publishTasks.value.find((task) => incompleteMultimodalItems(task).length > 0) || null
})

const multimodalTaskItems = computed<AssessmentPublishItemRecord[]>(() =>
  (activeMultimodalTask.value ? incompleteMultimodalItems(activeMultimodalTask.value) : [])
    .sort((a, b) => {
      if (a.id === routeTaskItemId.value) return -1
      if (b.id === routeTaskItemId.value) return 1
      return (a.order_no || 0) - (b.order_no || 0)
    }),
)
const multimodalTaskMode = computed(() => multimodalTaskItems.value.length > 0)
const activeMultimodalTaskTitle = computed(() => activeMultimodalTask.value?.batch_title || '发布测评任务')
const moduleStatusBadgeText = (completed: boolean) => {
  if (completed) return '已完成'
  return multimodalTaskMode.value ? '当前任务中' : '自由测评'
}
const moduleStatusBadgeClass = (completed: boolean, dark = false) => {
  if (completed) {
    return dark
      ? 'bg-emerald-500/20 text-emerald-300 ring-emerald-400/20'
      : 'bg-emerald-50 text-emerald-600 ring-emerald-100'
  }
  return dark
    ? 'bg-white/10 text-white/70 ring-white/15'
    : 'bg-white text-slate-500 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700'
}
const voiceMaxDuration = 10
const voiceRecordingProgress = computed(() => Math.min(100, Math.round((voiceDuration.value / voiceMaxDuration) * 100)))
const voiceStatusLabel = computed(() => {
  if (voiceCaptureState.value === 'recording') return '正在录音'
  if (voiceCaptureState.value === 'analyzing') return '分析中...'
  return '准备就绪'
})

const steps = [
  { id: 'scale' as const, label: '对话评估', icon: ClipboardList, done: scaleCompleted },
  { id: 'voice' as const, label: '语音识别', icon: Mic, done: voiceCompleted },
  { id: 'expression' as const, label: '表情识别', icon: Video, done: expressionCompleted },
]

const currentStepIndex = computed(() => Math.max(0, steps.findIndex((item) => item.id === step.value)))
const mobileStepTrackWidth = computed(() => `${(currentStepIndex.value / Math.max(1, steps.length - 1)) * 100}%`)

const progressValue = computed(() => {
  if (step.value === 'scale') return 33
  if (step.value === 'voice') return 66
  if (step.value === 'expression') return 88
  return 100
})

const voiceScore = computed(() => {
  if (!voiceCompleted.value || !voiceReport.value) return 0
  const sad = voiceReport.value.emotionVector.sad || 0
  const fearful = voiceReport.value.emotionVector.fearful || 0
  const pauseBonus = voiceReport.value.indicators.isLongPause ? 12 : 0
  return Math.min(94, Math.round(42 + sad * 34 + fearful * 28 + pauseBonus))
})

const expressionScore = computed(() => {
  if (!expressionCompleted.value || !expressionAiReport.value) return 0
  return Math.round(expressionAiReport.value.depression_risk_score)
})

const expressionStatusText = computed(() => {
  if (expressionStatus.value === 'idle') return '等待开始检测'
  if (expressionStatus.value === 'capturing') return `正在识别 · ${expressionCountdown.value}s`
  if (expressionStatus.value === 'analyzing') return 'AI分析中，请稍候...'
  return '表情识别完成'
})

const scaleSummary = computed<ModuleResult>(() => ({
  score: scaleScore.value,
  label: scaleResult.value?.riskLevel === 'high' ? '高风险' : scaleResult.value?.riskLevel === 'medium' ? '中风险' : '低风险',
  summary: `${selectedScales.value.join('、')} 对话量表得分 ${scaleResult.value?.score ?? 0}/27，原始分 ${scaleResult.value?.raw_score ?? 0}/${scaleResult.value?.max_raw_score ?? 0}，需要结合语音与表情分析进一步判断。`,
}))

const voiceSummary = computed<ModuleResult>(() => ({
  score: voiceScore.value,
  label: !voiceReport.value ? '未完成' : voiceScore.value >= 70 ? '语音波动较大' : voiceScore.value >= 55 ? '语音轻度波动' : '语音相对平稳',
  summary:
    voiceReport.value?.depressionAnalysis ||
    '语音模块尚未完成识别，请先录音或上传音频并等待分析结果。',
}))

const expressionSummary = computed<ModuleResult>(() => ({
  score: expressionScore.value,
  label: !expressionAiReport.value ? '未完成' : expressionScore.value >= 70 ? '面部收敛' : expressionScore.value >= 55 ? '轻度波动' : '表情较稳定',
  summary:
    expressionAiReport.value?.analysis_report ||
    '面部识别尚未获得有效报告，请重新采集清晰面部快照。',
}))

const calculateScaleNormalized = (scaleRaw: number) => {
  if (scaleRaw <= 4) return scaleRaw * 5
  if (scaleRaw <= 9) return 20 + (scaleRaw - 5) * 4
  if (scaleRaw <= 14) return 40 + (scaleRaw - 10) * 4
  if (scaleRaw <= 19) return 60 + (scaleRaw - 15) * 4
  return 80 + (scaleRaw - 20) * 2.5
}

const expressionRadarItems = computed(() => [
  { key: 'neutral', label: '中性', value: 0, tone: 'bg-slate-400' },
  { key: 'happy', label: '高兴', value: 0, tone: 'bg-amber-400' },
  { key: 'sad', label: '悲伤', value: 0, tone: 'bg-blue-500' },
  { key: 'angry', label: '愤怒', value: 0, tone: 'bg-rose-500' },
  { key: 'surprised', label: '惊讶', value: 0, tone: 'bg-cyan-500' },
  { key: 'fearful', label: '恐惧', value: 0, tone: 'bg-purple-500' },
  { key: 'disgusted', label: '厌恶', value: 0, tone: 'bg-emerald-500' },
  { key: 'contempt', label: '轻蔑', value: 0, tone: 'bg-orange-500' },
  { key: 'pain', label: '痛苦', value: 0, tone: 'bg-red-600' },
].map((item) => ({
  ...item,
  value: Number(expressionAiReport.value?.emotion_radar?.[item.key] ?? item.value),
})))

type RadarPoint = {
  key: string
  label: string
  value: number
  rawValue: number
  x: number
  y: number
  labelX: number
  labelY: number
}

const radarPoint = (
  item: { key: string; label: string; value: number; rawValue?: number },
  index: number,
  total: number,
  radius = 72,
): RadarPoint => {
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2
  const normalized = Math.min(1, Math.max(0, item.value))
  const pointRadius = radius * normalized
  const labelRadius = radius + 22
  return {
    key: item.key,
    label: item.label,
    value: normalized,
    rawValue: Number(item.rawValue ?? item.value),
    x: 100 + Math.cos(angle) * pointRadius,
    y: 100 + Math.sin(angle) * pointRadius,
    labelX: 100 + Math.cos(angle) * labelRadius,
    labelY: 100 + Math.sin(angle) * labelRadius,
  }
}

const radarPolygon = (points: RadarPoint[]) =>
  points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' ')

const voiceRadarItems = computed(() => {
  if (!voiceReport.value) return []
  const source = voiceReport.value.emotionVector
  const values = [
    { key: 'calm', label: '平静', isDepression: false, isHighlight: true },
    { key: 'happy', label: '高兴', isDepression: false, isHighlight: true },
    { key: 'sad', label: '悲伤', isDepression: true, isHighlight: false },
    { key: 'angry', label: '愤怒', isDepression: false, isHighlight: true },
    { key: 'surprised', label: '惊讶', isDepression: false, isHighlight: true },
    { key: 'fearful', label: '恐惧', isDepression: true, isHighlight: false },
    { key: 'disgusted', label: '厌恶', isDepression: false, isHighlight: false },
    { key: 'neutral', label: '中性', isDepression: false, isHighlight: true },
  ].map((item) => {
    const rawValue = Number(source[item.key] ?? 0)
    let adjustedValue = rawValue
    if (item.isDepression) adjustedValue = rawValue * 0.6
    else if (item.isHighlight) adjustedValue = Math.min(1, rawValue * 1.15)
    return { ...item, value: adjustedValue, rawValue }
  })

  const processedValues = values.map((item) => item.value)
  const maxValue = Math.max(...processedValues)
  const minValue = Math.min(...processedValues)
  const mapToRadius = (value: number, isHighlight: boolean) => {
    if (maxValue === minValue) return 0.6
    const normalized = (value - minValue) / (maxValue - minValue)
    const baseRadius = 0.3 + normalized * 0.6
    return isHighlight ? Math.min(1, baseRadius + 0.08) : baseRadius
  }

  return values.map((item, index) =>
    radarPoint(
      {
        key: item.key,
        label: item.label,
        value: mapToRadius(item.value, item.isHighlight),
        rawValue: item.rawValue,
      },
      index,
      values.length,
      72,
    ),
  )
})

const voiceRadarPolygon = computed(() => radarPolygon(voiceRadarItems.value))
const voiceRadarGrid = computed(() => [0.33, 0.66, 1].map((scale) =>
  radarPolygon(voiceRadarItems.value.map((item, index) => radarPoint({ ...item, value: scale }, index, voiceRadarItems.value.length, 72))),
))

const expressionRadarPoints = computed(() =>
  expressionRadarItems.value.map((item, index) => {
    const boosted = Math.min(1, Math.max(0.12, Math.pow(Math.max(0, Number(item.value)), 0.5) * 1.4))
    return radarPoint({ key: item.key, label: item.label, value: boosted, rawValue: Number(item.value) }, index, expressionRadarItems.value.length, 68)
  }),
)
const expressionRadarPolygon = computed(() => radarPolygon(expressionRadarPoints.value))
const expressionRadarGrid = computed(() => [0.33, 0.66, 1].map((scale) =>
  radarPolygon(expressionRadarPoints.value.map((item, index) => radarPoint({ ...item, value: scale }, index, expressionRadarPoints.value.length, 68))),
))

const reportCards = computed(() => {
  if (!report.value) return []
  return [
    { key: 'scale', title: '对话评估', item: report.value.scale },
    { key: 'voice', title: '语音识别', item: report.value.voice },
    { key: 'expression', title: '表情识别', item: report.value.expression },
  ]
})

const scaleRawScore = computed(() => scaleResult.value?.score ?? Math.round((scaleScore.value / 100) * 27))

const scaleAdviceText = computed(() => {
  const level = scaleResult.value?.riskLevel || 'low'
  if (level === 'high') return '您的得分反映出显著的抑郁倾向，建议尽快咨询专业管理员进行干预。'
  if (level === 'medium') return '您的得分反映出存在一定的心理压力，可以通过运动、社交和充足睡眠来调节。'
  return '您的得分反映出心理状态相对健康，请继续保持积极的生活方式。'
})

const fusionScore = computed(() => {
  if (!report.value) return 0
  return report.value.overall.score
})

const fusionRiskLevel = computed<'low' | 'medium' | 'high' | 'extreme'>(() => {
  if (fusionScore.value >= 80 || scaleRawScore.value >= 20) return 'extreme'
  if (fusionScore.value >= 60 || scaleRawScore.value >= 15) return 'high'
  if (fusionScore.value >= 40 || scaleRawScore.value >= 10) return 'medium'
  return 'low'
})

const riskTextMap = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  extreme: '极高风险',
}

const riskBadgeClass = computed(() => {
  if (fusionRiskLevel.value === 'extreme') return 'bg-rose-600'
  if (fusionRiskLevel.value === 'high') return 'bg-orange-500'
  if (fusionRiskLevel.value === 'medium') return 'bg-violet-500'
  return 'bg-emerald-500'
})

const professionalAdvice = computed(() => {
  if (reportAdvice.value) return reportAdvice.value
  return '该报告缺少 AI 多模态诊断结论，请重新完成多模态评估后生成完整报告。'
})

const extractFusionPayload = (response: any) => {
  const content = extractChatCompletionText(response)
  const jsonText = content.match(/\{[\s\S]*\}/)?.[0]
  if (!jsonText) throw new Error('AI 未返回AI多模态报告 JSON')
  const parsed = JSON.parse(jsonText)
  const fusedScore = Number(parsed.fused_score ?? parsed.score)
  const detailedReport = String(parsed.detailed_report || parsed.analysis || '').trim()
  if (!Number.isFinite(fusedScore)) throw new Error('AI 未返回有效融合分数')
  if (!detailedReport) throw new Error('AI 未返回 AI多模态报告结论')
  return {
    score: Math.max(0, Math.min(100, Math.round(fusedScore))),
    riskLevel: Number(parsed.risk_level),
    symptoms: parsed.symptoms || {},
    recommendations: Array.isArray(parsed.recommendations)
      ? parsed.recommendations.map((item: unknown) => String(item)).filter(Boolean)
      : [],
    detailedReport,
  }
}

const exportFusionReport = async (format: 'pdf' | 'png') => {
  try {
    await exportElementReport(fusionReportEl.value, format, 'AIMultimodalReport')
    statusMessage.value = '下载成功'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '下载失败'
  }
}

const exportVoiceReport = async (format: 'pdf' | 'png') => {
  try {
    await exportElementReport(voiceReportEl.value, format, 'voice-report', { signatureLine: format === 'pdf' })
    statusMessage.value = format === 'pdf' ? '语音报告PDF已下载' : '语音报告PNG已导出'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '语音报告导出失败'
  }
}

const exportScaleReport = async (format: 'pdf' | 'png') => {
  try {
    await exportElementReport(scaleReportEl.value, format, 'assessment-report')
    statusMessage.value = format === 'pdf' ? '量表报告PDF已下载' : '量表报告PNG已导出'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '量表报告导出失败'
  }
}

const normalizeScaleHistory = (value: any): ScaleResult => {
  const rawScore = Number(value?.score ?? value?.phq9_score ?? value?.raw_score ?? 0)
  const maxRawScore = Number(value?.max_raw_score ?? value?.maxRawScore ?? 27)
  const riskLevel = (value?.riskLevel || value?.risk_level || getScaleRiskLevel(rawScore)) as ScaleResult['riskLevel']
  const scaleTypes = Array.isArray(value?.scaleTypes)
    ? value.scaleTypes
    : Array.isArray(value?.scale_types)
      ? value.scale_types
      : selectedScales.value
  return {
    score: rawScore,
    phq9_score: Number(value?.phq9_score ?? rawScore),
    raw_score: Number(value?.raw_score ?? rawScore),
    max_raw_score: maxRawScore,
    riskLevel,
    risk_level: riskLevel,
    scaleTypes,
    dimensionScores: Array.isArray(value?.dimensionScores)
      ? value.dimensionScores
      : Array.isArray(value?.dimension_scores)
        ? value.dimension_scores
        : [
            { label: '兴趣丧失', score: Math.min(3, rawScore >= 15 ? 3 : 1), max: 3 },
            { label: '情绪低落', score: Math.min(3, rawScore >= 10 ? 2 : 1), max: 3 },
            { label: '睡眠问题', score: Math.min(3, rawScore >= 8 ? 2 : 0), max: 3 },
            { label: '疲劳感', score: Math.min(3, rawScore >= 6 ? 2 : 0), max: 3 },
            { label: '注意力', score: Math.min(3, rawScore >= 12 ? 2 : 1), max: 3 },
          ],
    conversationHistory: Array.isArray(value?.conversationHistory)
      ? value.conversationHistory
      : Array.isArray(value?.conversation_history)
        ? value.conversation_history
        : [],
  }
}

const hasUsableVoiceHistory = (value: any) => {
  const source = value?.reportData ? { ...value.reportData, duration: value.duration, waveform: value.waveform } : value
  const text = String(source?.text || source?.transcript || '').trim()
  const emotionVector = source?.emotionVector || source?.emotion_vector || source?.emotions
  const speechMetrics = source?.speechMetrics || source?.speech_metrics
  return Boolean(text && emotionVector && speechMetrics)
}

const hasUsableExpressionHistory = (value: any) => {
  const source = value?.reportData ?? value
  const radar = source?.emotion_radar || source?.facial_expressions
  const microFeatures = source?.micro_features
  return Boolean(
    radar &&
      typeof radar.neutral === 'number' &&
      typeof (source?.depression_risk_score ?? source?.risk_score) === 'number' &&
      String(source?.analysis_report || source?.analysis || '').trim() &&
      String(microFeatures?.brow_furrow || '').trim() &&
      String(microFeatures?.mouth_droop || '').trim() &&
      String(microFeatures?.eye_contact || '').trim(),
  )
}

const normalizeVoiceHistory = (value: any): VoiceReport | null => {
  if (!hasUsableVoiceHistory(value)) return null
  const source = value?.reportData ? { ...value.reportData, duration: value.duration, waveform: value.waveform } : value || {}
  const emotionVector = source.emotionVector || source.emotion_vector || source.emotions || {}
  const speechMetrics = source.speechMetrics || source.speech_metrics || {}
  const normalizedVector = {
    calm: Number(emotionVector.calm ?? 0),
    happy: Number(emotionVector.happy ?? 0),
    sad: Number(emotionVector.sad ?? 0),
    angry: Number(emotionVector.angry ?? 0),
    surprised: Number(emotionVector.surprised ?? emotionVector.surprise ?? 0),
    fearful: Number(emotionVector.fearful ?? emotionVector.fear ?? 0),
    disgusted: Number(emotionVector.disgusted ?? 0),
    neutral: Number(emotionVector.neutral ?? 0),
  }
  return {
    text: String(source.text || source.transcript || ''),
    confidence: Number(source.confidence ?? 0),
    emotionVector: normalizedVector,
    speechMetrics: {
      speed: String(speechMetrics.speed ?? source.speech_rate ?? ''),
      tone: String(speechMetrics.tone ?? source.pitch_variation ?? ''),
      pause: String(speechMetrics.pause ?? source.pause_frequency ?? ''),
      energy: String(speechMetrics.energy ?? ''),
    },
    indicators: {
      isLowSpeed: Boolean(source.indicators?.isLowSpeed ?? source.indicators?.is_low_speed ?? false),
      isHighPitchDrop: Boolean(source.indicators?.isHighPitchDrop ?? source.indicators?.is_high_pitch_drop ?? false),
      isLongPause: Boolean(source.indicators?.isLongPause ?? source.indicators?.is_long_pause ?? false),
    },
    depressionAnalysis: String(source.depressionAnalysis || source.depression_analysis || source.analysis || ''),
  }
}

const normalizeExpressionHistory = (value: any): ExpressionAiReport | null => {
  if (!hasUsableExpressionHistory(value)) return null
  const source = value?.reportData ?? value ?? {}
  const radar = source.emotion_radar || source.facial_expressions || {}
  return {
    emotion_radar: {
      neutral: Number(radar.neutral ?? 0),
      happy: Number(radar.happy ?? 0),
      sad: Number(radar.sad ?? 0),
      angry: Number(radar.angry ?? 0),
      surprised: Number(radar.surprised ?? 0),
      fearful: Number(radar.fearful ?? 0),
      disgusted: Number(radar.disgusted ?? 0),
      contempt: Number(radar.contempt ?? 0),
      pain: Number(radar.pain ?? 0),
    },
    depression_risk_score: Number(source.depression_risk_score ?? source.risk_score),
    analysis_report: String(source.analysis_report || source.analysis || ''),
    micro_features: {
      brow_furrow: String(source.micro_features?.brow_furrow || ''),
      mouth_droop: String(source.micro_features?.mouth_droop || ''),
      eye_contact: String(source.micro_features?.eye_contact || ''),
    },
  }
}

const loadFusionHistoryItem = (item: any) => {
  const raw = item.report || {}
  const fusionAi = raw.fusionAi || raw.fusion_ai || {}
  const fusionRecommendations = Array.isArray(fusionAi.recommendations)
    ? fusionAi.recommendations.map((entry: unknown, index: number) => `${index + 1}. ${String(entry)}`).join('\n')
    : ''
  const aiAdvice = String(
    raw.advice ||
      raw.overall?.advice ||
      fusionRecommendations ||
      fusionAi.detailedReport ||
      fusionAi.detailed_report ||
      item.overall?.summary ||
      raw.overall?.summary ||
      '',
  ).trim()
  const nextScale = normalizeScaleHistory(raw.scaleData || raw.scale || item.scale)
  const nextVoice = normalizeVoiceHistory(raw.voiceData || raw.voice || item.voice)
  const nextExpression = normalizeExpressionHistory(raw.expressionData || raw.expression || item.expression)
  if (!nextVoice || !nextExpression) {
    errorMessage.value = '该历史报告缺少语音转写或面部分析结果，不能作为完整AI多模态报告载入'
    return
  }
  const nextOverall = item.overall || raw.overall || {
    score: item.score ?? 0,
    label: '历史AI多模态报告',
    summary: '已载入历史AI多模态报告。',
  }

  scaleResult.value = nextScale
  selectedScales.value = nextScale.scaleTypes.length > 0 ? nextScale.scaleTypes : selectedScales.value
  voiceReport.value = nextVoice
  voiceRecognizedText.value = nextVoice.text
  expressionAiReport.value = nextExpression
  expressionDominantEmotion.value = expressionRadarItems.value.reduce((max, current) => (current.value > max.value ? current : max), expressionRadarItems.value[0]!).label
  scaleCompleted.value = true
  voiceCompleted.value = true
  expressionCompleted.value = true
  report.value = {
    scale: item.scale || scaleSummary.value,
    voice: item.voice || voiceSummary.value,
    expression: item.expression || expressionSummary.value,
    overall: {
      score: Number(nextOverall.score ?? item.score ?? 0),
      label: String(nextOverall.label ?? '历史AI多模态报告'),
      summary: String(nextOverall.summary ?? raw.advice ?? '已载入历史AI多模态报告。'),
    },
  }
  reportAdvice.value = aiAdvice
  reportGeneratedAt.value = item.createdAt || new Date().toLocaleString('zh-CN')
  fusionHistoryOpen.value = false
  statusMessage.value = '历史报告已载入'
}

const openFusionHistory = async () => {
  fusionHistoryOpen.value = true
  fusionHistoryLoading.value = true
  errorMessage.value = ''
  try {
    await refreshAssessments()
  } catch (error) {
    errorMessage.value = error instanceof Error ? `历史记录加载失败：${error.message}` : '历史记录加载失败'
  } finally {
    fusionHistoryLoading.value = false
  }
}

const ensureQuestionMark = (question: string) => {
  const trimmed = question.trim()
  if (!trimmed) return trimmed
  return /[？?]$/.test(trimmed) ? trimmed : `${trimmed}？`
}

const scoreAnswer = (content: string) => {
  const text = content.trim()
  if (/(完全没有|没有|从不|并不|0\s*分)/.test(text)) return 0
  if (/(几天|偶尔|有一点|轻微|1\s*分)/.test(text)) return 1
  if (/(一半|经常|比较|明显|2\s*分)/.test(text)) return 2
  if (/(几乎每天|每天|总是|严重|非常|不想活|自杀|轻生|死亡|3\s*分)/.test(text)) return 3
  if (/(难受|崩溃|绝望|无助|低落|焦虑|睡不着|疲惫)/.test(text)) return 2
  return 1
}

const getScaleRiskLevel = (score: number): ScaleResult['riskLevel'] => {
  if (score >= 20) return 'high'
  if (score >= 10) return 'medium'
  return 'low'
}

const getQuestionAt = (index: number) => {
  const bank = scaleQuestionBank.value.length > 0
    ? scaleQuestionBank.value
    : selectedScales.value.flatMap((id) => builtinScaleQuestions[id] ?? [])
  return ensureQuestionMark(bank[index] ?? bank[bank.length - 1] ?? '请描述一下您最近两周的心情与兴趣变化')
}

const scrollScaleMessages = () => {
  void nextTick(() => {
    if (scaleMessagesEl.value) {
      scaleMessagesEl.value.scrollTop = scaleMessagesEl.value.scrollHeight
    }
  })
}

const clearScaleTyping = () => {
  if (scaleTypingTimer !== null) {
    window.clearTimeout(scaleTypingTimer)
    scaleTypingTimer = null
  }
  scaleTypingMessageIndex.value = null
  scaleTypingText.value = ''
}

const startScaleTyping = (messageIndex: number) => {
  clearScaleTyping()
  const message = scaleMessages.value[messageIndex]
  if (!message || message.role !== 'assistant') return
  const fullText = message.content
  const chars = Array.from(fullText)
  let cursor = 0
  scaleTypingMessageIndex.value = messageIndex
  scaleTypingText.value = ''

  const tick = () => {
    if (scaleMessages.value[messageIndex]?.content !== fullText) {
      clearScaleTyping()
      return
    }
    if (cursor >= chars.length) {
      clearScaleTyping()
      scrollScaleMessages()
      return
    }
    const char = chars[cursor] || ''
    cursor += 1
    scaleTypingText.value = chars.slice(0, cursor).join('')
    scrollScaleMessages()
    const delay = /[\s，。！？、：；""''（）【】—…]/.test(char)
      ? 5
      : /[\u4e00-\u9fa5]/.test(char)
        ? 18
        : 12
    scaleTypingTimer = window.setTimeout(tick, delay)
  }

  tick()
}

const loadScaleSession = (): ScaleSessionDraft | null => {
  try {
    pruneScaleSessions()
    const raw = window.localStorage.getItem(currentScaleSessionKey.value)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ScaleSessionDraft
    if (!Array.isArray(parsed.messages) || parsed.messages.length === 0) return null
    if (!Array.isArray(parsed.selectedScales) || parsed.selectedScales.length === 0) return null
    if (parsed.completed) return null
    if (parsed.version && parsed.version !== SCALE_SESSION_VERSION) return null
    if (parsed.userId && state.currentAccountId && parsed.userId !== state.currentAccountId) return null
    if (parsed.updatedAt && Date.now() - new Date(parsed.updatedAt).getTime() > SCALE_SESSION_MAX_AGE_DAYS * 24 * 60 * 60 * 1000) {
      window.localStorage.removeItem(currentScaleSessionKey.value)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

const saveScaleSession = () => {
  if (!scaleStarted.value || scaleCompleted.value || scaleMessages.value.length === 0) return
  const draft: ScaleSessionDraft = {
    version: SCALE_SESSION_VERSION,
    userId: state.currentAccountId || undefined,
    updatedAt: new Date().toISOString(),
    completed: false,
    selectedScales: [...selectedScales.value],
    questionIndex: scaleQuestionIndex.value,
    totalQuestions: scaleTotalQuestions.value,
    questionBank: [...scaleQuestionBank.value],
    messages: scaleMessages.value.map((message) => ({
      role: message.role,
      content: message.content,
      timestamp: message.timestamp.toISOString(),
    })),
  }
  window.localStorage.setItem(currentScaleSessionKey.value, JSON.stringify(draft))
}

const clearScaleSession = () => {
  window.localStorage.removeItem(currentScaleSessionKey.value)
  window.localStorage.removeItem(legacyScaleSessionKey)
  scaleResumeBanner.value = false
}

const pruneScaleSessions = () => {
  if (!state.currentAccountId) return
  const keysToRemove: string[] = []
  for (let index = 0; index < window.localStorage.length; index += 1) {
    const key = window.localStorage.key(index)
    if (!key || !key.startsWith('mindcare_assessment_session_')) continue
    if (!key.includes(`_${SCALE_SESSION_VERSION}_`)) {
      keysToRemove.push(key)
      continue
    }
    if (!key.endsWith(`_${state.currentAccountId}`)) continue
    try {
      const raw = window.localStorage.getItem(key)
      if (!raw) continue
      const parsed = JSON.parse(raw) as ScaleSessionDraft
      const expired = parsed.updatedAt
        ? Date.now() - new Date(parsed.updatedAt).getTime() > SCALE_SESSION_MAX_AGE_DAYS * 24 * 60 * 60 * 1000
        : false
      if (parsed.completed || expired) keysToRemove.push(key)
    } catch {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach((key) => window.localStorage.removeItem(key))
}

const resumeScaleSession = () => {
  clearScaleTyping()
  const draft = loadScaleSession()
  if (!draft) {
    clearScaleSession()
    return
  }
  selectedScales.value = draft.selectedScales.filter((scale): scale is ScaleId => ['PHQ-9', 'HAMD-17', 'SDS-20'].includes(scale))
  if (selectedScales.value.length === 0) selectedScales.value = ['PHQ-9']
  scaleQuestionBank.value = Array.isArray(draft.questionBank) && draft.questionBank.length > 0
    ? draft.questionBank
    : selectedScales.value.flatMap((id) => builtinScaleQuestions[id] ?? [])
  scaleTotalQuestions.value = Math.max(1, Number(draft.totalQuestions || scaleQuestionBank.value.length || 1))
  scaleQuestionIndex.value = Math.min(Number(draft.questionIndex || 0), scaleTotalQuestions.value)
  scaleMessages.value = draft.messages.map((message) => ({
    role: message.role,
    content: message.content,
    timestamp: new Date(message.timestamp),
  }))
  scaleStarted.value = true
  scaleCompleted.value = false
  scaleResult.value = null
  scaleResumeBanner.value = false
  statusMessage.value = '已恢复上次未完成的评估'
  scrollScaleMessages()
}

const cleanAiText = (text: string) =>
  text
    .replace(/^[A-Za-z]\s*(\n|$)+/, '')
    .replace(/^(hi|hello)[,，!\s]+/i, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n')
    .map((line) => line.trim())
    .join('\n')
    .trim()

const extractChatCompletionText = (response: any) => {
  const choice = response?.choices?.[0]
  return cleanAiText(String(
    choice?.message?.content ||
      choice?.delta?.content ||
      response?.content ||
      response?.text ||
      response?.result ||
      '',
  ))
}

const buildScaleAssessmentReply = (userResponse: string, nextQuestion: string, nextQuestionNumber: number) => {
  const response = userResponse.toLowerCase()
  let prefix = ''

  if (response.includes('经常') || response.includes('总是') || response.includes('每天')) {
    prefix = '我记下了，这种情况出现得比较频繁。'
  } else if (response.includes('偶尔') || response.includes('有时') || response.includes('不太')) {
    prefix = '我记下了，这种情况是间歇出现的。'
  } else if (response.includes('没有') || response.includes('不会') || response.includes('很少')) {
    prefix = '我记下了，目前这方面影响相对较轻。'
  } else if (response.includes('不确定') || response.includes('不知道')) {
    prefix = '没关系，按最近两周的大致感受回答就可以。'
  } else if (response.includes('失眠') || response.includes('睡不着')) {
    prefix = '我记下了，睡眠方面的变化需要重点关注。'
  } else if (response.includes('压力') || response.includes('焦虑')) {
    prefix = '我记下了，你刚才提到了压力和焦虑。'
  } else if (response.includes('难过') || response.includes('伤心') || response.includes('沮丧')) {
    prefix = '我记下了，这类情绪体验值得继续了解。'
  } else if (response.length > 20) {
    prefix = '我记下了你刚才提到的情况。'
  } else {
    prefix = '我记下了。'
  }

  return `${prefix} 下面继续第${nextQuestionNumber}题：${nextQuestion}`
}

const buildScaleCompletionMessages = (userResponse: string) => {
  const result = buildScaleResult([...scaleMessages.value, { role: 'user', content: userResponse, timestamp: new Date() }])
  const history = scaleMessages.value.slice(-14).map((message) => ({
    role: message.role,
    content: message.content,
  }))
  return [
    {
      role: 'system' as const,
      content: [
        '你是初心的心理对话评估助手，刚完成一轮对话式心理评估。',
        '请基于对话历史和量表计分结果给出简短收束语，不要编造没有依据的诊断。',
        '必须包含：评估已完成、分数、风险等级、下一步建议。不要输出 JSON 或 Markdown。',
        `量表：${selectedScales.value.join('、')}`,
        `分数：${result.score}`,
        `风险等级：${scaleRiskInfo(result.riskLevel).label}`,
      ].join('\n'),
    },
    ...history,
    { role: 'user' as const, content: userResponse },
  ]
}

const requestScaleCompletionReply = async (userResponse: string) => {
  const response = await chatCompletion(buildScaleCompletionMessages(userResponse))
  const content = extractChatCompletionText(response)
  if (!content) throw new Error('AI 未返回量表完成总结')
  return content
}

const formatScaleHistoryDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const scaleRiskInfo = (level: 'low' | 'medium' | 'high') => {
  if (level === 'high') return { label: '高风险', badge: 'bg-rose-50 text-rose-500 border-rose-100', solid: 'bg-[#F97316]' }
  if (level === 'medium') return { label: '中风险', badge: 'bg-amber-50 text-amber-500 border-amber-100', solid: 'bg-[#8B5CF6]' }
  return { label: '低风险', badge: 'bg-emerald-50 text-emerald-500 border-emerald-100', solid: 'bg-[#10B981]' }
}

const scaleHistoryDimensions = (history: HistoryScaleAssessment) => (
  history.reportData.dimensionScores || [
    { label: '兴趣丧失', score: Math.min(3, history.score >= 15 ? 3 : history.score >= 8 ? 2 : 1), max: 3 },
    { label: '情绪低落', score: Math.min(3, history.score >= 10 ? 2 : 1), max: 3 },
    { label: '睡眠问题', score: Math.min(3, history.score >= 8 ? 2 : 0), max: 3 },
    { label: '疲劳感', score: Math.min(3, history.score >= 6 ? 2 : 0), max: 3 },
    { label: '注意力', score: Math.min(3, history.score >= 12 ? 2 : 1), max: 3 },
    { label: '自杀意念', score: history.score >= 20 ? 2 : 0, max: 3 },
  ]
)

const openScaleHistoryDetail = (history: HistoryScaleAssessment) => {
  selectedScaleHistory.value = history
  scaleHistoryOpen.value = false
  scaleHistoryDetailOpen.value = true
}

const closeScaleHistoryDetail = (openList = true) => {
  scaleHistoryDetailOpen.value = false
  if (openList) scaleHistoryOpen.value = true
}

const buildQuestionBankFromKnowledge = (items: Array<{ title?: string; content?: string; tags?: string[] | null }>) => {
  const parsed = items.flatMap((item) => {
    try {
      const content = JSON.parse(item.content || '{}') as { scale_id?: string; questions?: Array<{ text?: string; order?: number }> }
      const candidate = [content.scale_id || '', item.title || '', ...((item.tags || []) as string[])].join(' ')
      const scaleId = /PHQ-?9/i.test(candidate)
        ? 'PHQ-9'
        : /HAMD-?17/i.test(candidate)
          ? 'HAMD-17'
          : /SDS-?20/i.test(candidate)
            ? 'SDS-20'
            : null
      if (!scaleId) return []
      const questions = Array.isArray(content.questions)
        ? content.questions
            .slice()
            .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
            .map((question) => String(question.text || '').trim())
            .filter(Boolean)
        : []
      return [{ scaleId, questions }]
    } catch {
      return []
    }
  })
  return selectedScales.value.flatMap((scaleId) => {
    const builtin = builtinScaleQuestions[scaleId] ?? []
    const candidate = parsed
      .filter((item) => item.scaleId === scaleId)
      .sort((a, b) => b.questions.length - a.questions.length)[0]
    return candidate && candidate.questions.length >= builtin.length ? candidate.questions.slice(0, builtin.length) : builtin
  })
}

const loadScaleQuestionBank = async () => {
  try {
    const kb = await getKnowledgeBase('assessment')
    const questions = buildQuestionBankFromKnowledge(kb)
    scaleQuestionBank.value = questions.length > 0 ? questions : selectedScales.value.flatMap((id) => builtinScaleQuestions[id] ?? [])
  } catch {
    scaleQuestionBank.value = selectedScales.value.flatMap((id) => builtinScaleQuestions[id] ?? [])
  }
  scaleTotalQuestions.value = Math.max(1, scaleQuestionBank.value.length)
}

const toggleScale = (id: ScaleId) => {
  if (scaleStarted.value) return
  selectedScales.value = selectedScales.value.includes(id)
    ? selectedScales.value.filter((item) => item !== id)
    : [...selectedScales.value, id]
  if (selectedScales.value.length === 0) selectedScales.value = [id]
}

const startScaleAssessment = async () => {
  clearScaleTyping()
  clearScaleReadTimer()
  clearScaleSession()
  scaleCompleted.value = false
  scaleReportOpen.value = false
  scaleReadCountdown.value = 0
  scaleResult.value = null
  await loadScaleQuestionBank()
  scaleStarted.value = true
  scaleQuestionIndex.value = 0
  scaleMessages.value = [{
    role: 'assistant',
    content: `你好，我是初心心理助手。接下来我们会一起完成 ${selectedScales.value.join('、')} 评估，我会根据你的回答一步一步陪你完成。第1题：${getQuestionAt(0)}`,
    timestamp: new Date(),
  }]
  startScaleTyping(0)
  scrollScaleMessages()
}

const retakeScaleAssessment = () => {
  clearScaleTyping()
  clearScaleReadTimer()
  clearScaleSession()
  scaleCompleted.value = false
  scaleStarted.value = false
  scaleResult.value = null
  scaleMessages.value = []
  scaleInputText.value = ''
  scaleQuestionIndex.value = 0
  scaleReportOpen.value = false
  statusMessage.value = '可重新开始对话评估，最终报告将保留最新一次结果'
}

const retakeExpressionAssessment = () => {
  clearExpressionTimers()
  expressionStatus.value = 'idle'
  expressionProgress.value = 0
  expressionCountdown.value = 5
  expressionCompleted.value = false
  expressionReportOpen.value = false
  expressionAiReport.value = null
  expressionSnapshot.value = ''
  statusMessage.value = '可重新进行表情识别，最终报告将保留最新一次结果'
}

const buildScaleResult = (messages = scaleMessages.value): ScaleResult => {
  const userAnswers = messages.filter((message) => message.role === 'user')
  const answerScores: number[] = userAnswers.slice(0, scaleTotalQuestions.value).map((message) => scoreAnswer(message.content))
  const maxRawScore = Math.max(1, scaleTotalQuestions.value * 3)
  const rawScore = answerScores.reduce((sum, value) => sum + value, 0)
  const normalizedScore = Math.min(27, Math.round((rawScore / maxRawScore) * 27))
  const level = getScaleRiskLevel(normalizedScore)
  const labels = (scaleQuestionBank.value.length > 0 ? scaleQuestionBank.value : selectedScales.value.flatMap((id) => builtinScaleQuestions[id] ?? []))
    .slice(0, 9)
    .map((question) => question.split(/[：:]/)[0] || question.slice(0, 6))
  return {
    score: normalizedScore,
    phq9_score: normalizedScore,
    raw_score: rawScore,
    max_raw_score: maxRawScore,
    riskLevel: level,
    risk_level: level,
    scaleTypes: [...selectedScales.value],
    dimensionScores: labels.map((label, index) => ({ label, score: answerScores[index] ?? 0, max: 3 })),
    conversationHistory: messages.map((message) => ({
      role: message.role,
      content: message.content,
      timestamp: message.timestamp.toISOString(),
    })),
  }
}

const finishScaleAssessment = (messages = scaleMessages.value) => {
  scaleResult.value = buildScaleResult(messages)
  scaleCompleted.value = true
  scaleReportOpen.value = true
  clearScaleReadTimer()
  if (scaleResult.value.riskLevel === 'high' || scaleResult.value.riskLevel === 'medium') {
    scaleReadCountdown.value = 10
    scaleReadTimer = setInterval(() => {
      scaleReadCountdown.value = Math.max(0, scaleReadCountdown.value - 1)
      if (scaleReadCountdown.value === 0) clearScaleReadTimer()
    }, 1000)
  }
  clearScaleSession()
  statusMessage.value = '对话评估已完成'
}

function clearScaleReadTimer() {
  if (scaleReadTimer) {
    clearInterval(scaleReadTimer)
    scaleReadTimer = null
  }
}

const openVoiceAssessmentFromScale = () => {
  if (scaleReadCountdown.value > 0) return
  scaleReportOpen.value = false
  clearScaleReadTimer()
  step.value = 'voice'
  statusMessage.value = '请开始语音情绪识别'
  if (voiceCaptureState.value === 'idle') {
    void startVoiceCapture()
  }
  void nextTick(() => {
    document.querySelector('[data-testid="voice-status-panel"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="assessment-voice-record"]')
    recordButton?.focus({ preventScroll: true })
  })
}

const sendScaleResponse = async (response?: string) => {
  const text = (response ?? scaleInputText.value).trim()
  if (!text || scaleInteractionLocked.value || scaleCompleted.value) return
  clearScaleTyping()
  if (scaleVoiceListening.value) stopScaleVoiceInput()
  scaleEmojiPickerOpen.value = false
  scaleLoading.value = true
  scaleInputText.value = ''
  const userMsg: ScaleMessage = { role: 'user', content: text, timestamp: new Date() }
  const nextIndex = scaleQuestionIndex.value + 1
  const hasNext = nextIndex < scaleTotalQuestions.value
  const previousMessages = [...scaleMessages.value]
  scaleMessages.value = [...previousMessages, userMsg]
  scrollScaleMessages()
  let assistantContent = ''
  try {
    if (hasNext) {
      assistantContent = buildScaleAssessmentReply(text, getQuestionAt(nextIndex), nextIndex + 1)
    } else {
      assistantContent = await requestScaleCompletionReply(text)
    }
  } catch (error) {
    scaleMessages.value = previousMessages
    scaleInputText.value = text
    errorMessage.value = error instanceof Error ? `AI主动式量表对话失败：${error.message}` : 'AI主动式量表对话失败，请稍后重试'
    scaleLoading.value = false
    scrollScaleMessages()
    return
  }
  const assistantMsg: ScaleMessage = {
    role: 'assistant',
    content: assistantContent,
    timestamp: new Date(),
  }
  const assistantIndex = scaleMessages.value.length
  const nextMessages = [...scaleMessages.value, assistantMsg]
  const distress = /(崩溃|绝望|无助|很痛|难受|不想活|自杀|死亡)/.test(text)
  if (distress) {
    nextMessages.push({
      role: 'assistant',
      content: '【安全预警】检测到您可能存在自杀风险。我们非常关心您的安全。如果您正处于危险中，请立即拨打心理援助热线 400-161-9995 或联系紧急联系人。',
      timestamp: new Date(),
    })
  }
  if (/(不确定|不太清楚|说不清|不知道)/.test(text)) {
    nextMessages.push({
      role: 'assistant',
      content: '为了更准确评估，我来帮你澄清一下：在过去两周，出现该情况的频率更接近"几天"还是"超过一半天"？',
      timestamp: new Date(),
    })
  }
  scaleMessages.value = nextMessages
  scaleQuestionIndex.value = Math.min(nextIndex, scaleTotalQuestions.value)
  startScaleTyping(assistantIndex)
  if (hasNext) {
    void nextTick(saveScaleSession)
  }
  scrollScaleMessages()
  if (!hasNext) finishScaleAssessment(nextMessages)
  scaleLoading.value = false
}

const appendScaleEmoji = (emoji: string) => {
  if (scaleInteractionLocked.value) return
  scaleInputText.value = `${scaleInputText.value}${emoji}`
  scaleEmojiPickerOpen.value = false
}

const stopScaleVoiceStream = () => {
  scaleVoiceStream?.getTracks().forEach((track) => track.stop())
  scaleVoiceStream = null
}

const appendScaleVoiceText = (text: string) => {
  const normalized = text.trim()
  if (!normalized) return
  scaleInputText.value = `${scaleInputText.value}${scaleInputText.value.trim() ? ' ' : ''}${normalized}`.trimStart()
}

const startScaleBrowserSpeechShadow = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) return
  try {
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = false
    recognition.lang = 'zh-CN'
    recognition.onresult = (event: any) => {
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index]
        const transcript = String(result?.[0]?.transcript || '').trim()
        if (result?.isFinal && transcript) {
          scaleVoiceBrowserText = `${scaleVoiceBrowserText}${scaleVoiceBrowserText ? ' ' : ''}${transcript}`.trim()
        }
      }
    }
    recognition.onerror = () => undefined
    recognition.onend = () => {
      if (scaleVoiceListening.value) {
        try {
          recognition.start()
        } catch {
          scaleSpeechRecognition = null
        }
      }
    }
    recognition.start()
    scaleSpeechRecognition = recognition
  } catch {
    scaleSpeechRecognition = null
  }
}

const stopScaleBrowserSpeechShadow = () => {
  if (!scaleSpeechRecognition) return
  try {
    scaleSpeechRecognition.stop()
  } catch {
    // Browser speech recognition can already be stopped.
  }
  scaleSpeechRecognition = null
}

const requestScaleSpeechText = async (blob: Blob) => {
  const base64 = await blobToBase64(blob)
  const result = await speechRecognition(base64, inferAudioFormat(blob), 16000, blob.size)
  return String(result?.text || result?.result?.[0] || '').trim()
}

const transcribeScaleVoiceBlob = async (blob: Blob) => {
  if (!blob || blob.size <= 0) {
    throw new Error('未采集到有效音频')
  }
  const shouldConvertToWav = /webm|ogg|opus/i.test(blob.type || '')
  const wavBlob = shouldConvertToWav ? await convertWebmToWav(blob) : blob
  let text = await requestScaleSpeechText(wavBlob)
  if (!text && shouldConvertToWav) {
    text = await requestScaleSpeechText(blob)
  }
  if (!text) {
    return false
  }
  appendScaleVoiceText(text)
  return true
}

const analyzeScaleVoiceRecording = async () => {
  if (scaleVoiceAsrBusy) return
  const chunks = [...scaleVoiceChunks]
  scaleVoiceChunks = []
  if (chunks.length === 0) {
    errorMessage.value = '没有采集到语音，请重新录制'
    return
  }
  scaleVoiceAsrBusy = true
  scaleVoiceBusy.value = true
  const recording = new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' })
  await transcribeScaleVoiceBlob(recording)
    .then((recognized) => {
      scaleVoiceAsrErrorCount = 0
      if (!recognized) {
        if (scaleVoiceBrowserText.trim()) {
          appendScaleVoiceText(scaleVoiceBrowserText)
          scaleVoiceBrowserText = ''
          statusMessage.value = '语音识别完成'
        } else {
          statusMessage.value = '未识别到文字，请再录一次或直接输入'
        }
      }
    })
    .catch((error) => {
      scaleVoiceAsrErrorCount += 1
      if (scaleVoiceBrowserText.trim()) {
        appendScaleVoiceText(scaleVoiceBrowserText)
        scaleVoiceBrowserText = ''
        statusMessage.value = '语音识别完成'
        return
      }
      errorMessage.value = error instanceof Error ? `量表语音输入失败：${error.message}` : '量表语音输入失败'
    })
    .finally(() => {
      scaleVoiceAsrBusy = false
      scaleVoiceBusy.value = false
    })
}

const stopScaleVoiceInput = () => {
  if (!scaleVoiceListening.value) return
  scaleVoiceStopRequested = true
  scaleVoiceListening.value = false
  stopScaleBrowserSpeechShadow()
  if (scaleVoiceRecorder && scaleVoiceRecorder.state !== 'inactive') {
    scaleVoiceRecorder.stop()
  } else {
    stopScaleVoiceStream()
  }
}

const startScaleWebSpeechFallback = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    throw new Error('浏览器不支持实时识别且语音服务不可用')
  }
  const recognition = new SpeechRecognition()
  recognition.continuous = false
  recognition.interimResults = false
  recognition.lang = 'zh-CN'
  recognition.onresult = (event: any) => {
    const text = Array.from(event.results || [])
      .map((result: any) => result?.[0]?.transcript || '')
      .join('')
    appendScaleVoiceText(text)
  }
  recognition.onerror = () => {
    errorMessage.value = '语音输入失败，请改用文字输入'
  }
  recognition.onend = () => {
    scaleVoiceListening.value = false
    scaleVoiceBusy.value = false
  }
  scaleVoiceListening.value = true
  recognition.start()
}

const startScaleVoiceInput = async () => {
  if (scaleVoiceListening.value) {
    stopScaleVoiceInput()
    return
  }
  errorMessage.value = ''
  scaleVoiceBusy.value = false
  scaleVoiceAsrBusy = false
  scaleVoiceAsrErrorCount = 0
  scaleVoiceStopRequested = false
  scaleVoiceChunks = []
  scaleVoiceBrowserText = ''
  stopScaleBrowserSpeechShadow()

  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      errorMessage.value = '当前页面无法开启麦克风，请使用 HTTPS 访问'
      startScaleWebSpeechFallback()
      return
    }
    scaleVoiceStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
    scaleVoiceRecorder = new MediaRecorder(scaleVoiceStream, { mimeType: 'audio/webm;codecs=opus' })
    scaleVoiceRecorder.ondataavailable = (event) => {
      if (event.data?.size > 0) scaleVoiceChunks.push(event.data)
    }
    scaleVoiceRecorder.onstop = () => {
      stopScaleVoiceStream()
      void analyzeScaleVoiceRecording()
      scaleVoiceRecorder = null
    }
    scaleVoiceRecorder.start()
    scaleVoiceListening.value = true
    startScaleBrowserSpeechShadow()
  } catch (error) {
    stopScaleVoiceStream()
    stopScaleBrowserSpeechShadow()
    scaleVoiceListening.value = false
    scaleVoiceChunks = []
    try {
      startScaleWebSpeechFallback()
    } catch {
      errorMessage.value = error instanceof Error ? `量表语音输入失败：${error.message}` : '量表语音输入失败，请改用文字输入'
    }
  }
}

const refreshWaveform = () => {
  voiceWaveform.value = voiceWaveform.value.map((_, index) => {
    const base = 18 + Math.abs(Math.sin(Date.now() / 95 + index * 0.42)) * 65
    const boost = index > 25 ? 12 : 0
    return Math.round(Math.min(95, base + boost))
  })
}

const stopMicStream = () => {
  micStream?.getTracks().forEach((track) => track.stop())
  micStream = null
  if (audioContext) {
    void audioContext.close().catch(() => undefined)
    audioContext = null
  }
  analyser = null
  if (waveformFrame) {
    cancelAnimationFrame(waveformFrame)
    waveformFrame = 0
  }
}

const clearVoiceTimers = () => {
  if (voiceTimer) {
    clearInterval(voiceTimer)
    voiceTimer = null
  }
  if (voiceProgressTimer) {
    clearInterval(voiceProgressTimer)
    voiceProgressTimer = null
  }
}

const inferAudioFormat = (blob: Blob): 'wav' | 'm4a' | 'webm' | 'ogg' | 'mp3' => {
  const type = blob.type.toLowerCase()
  if (type.includes('webm')) return 'webm'
  if (type.includes('ogg')) return 'ogg'
  if (type.includes('mpeg') || type.includes('mp3')) return 'mp3'
  if (type.includes('mp4') || type.includes('m4a')) return 'm4a'
  return 'wav'
}

const decodeAudioBuffer = async (blob: Blob) => {
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
  const audioCtx = new AudioContextClass()
  try {
    const arrayBuffer = await blob.arrayBuffer()
    return await audioCtx.decodeAudioData(arrayBuffer)
  } finally {
    await audioCtx.close().catch(() => undefined)
  }
}

const normalizeEmotionVector = (raw: any): Record<string, number> => {
  const keys = ['calm', 'happy', 'sad', 'angry', 'surprised', 'fearful', 'disgusted', 'neutral']
  const values = Object.fromEntries(keys.map((key) => [key, Math.max(0, Number(raw?.[key] ?? 0))])) as Record<string, number>
  const sum = keys.reduce((total, key) => total + (values[key] ?? 0), 0)
  if (sum <= 0) throw new Error('AI 未返回有效情绪向量')
  return Object.fromEntries(keys.map((key) => [key, (values[key] ?? 0) / sum])) as Record<string, number>
}

const parseVoiceAiResult = (content: string) => {
  const jsonText = content.match(/\{[\s\S]*\}/)?.[0]
  if (!jsonText) throw new Error('AI 未返回语音情绪 JSON')
  const parsed = JSON.parse(jsonText)
  const emotionVector = normalizeEmotionVector(parsed.emotion_vector)
  const confidence = Number(parsed.confidence)
  const depressionAnalysis = String(parsed.depression_analysis || parsed.analysis || '').trim()
  const indicators = parsed.indicators || {}
  if (!depressionAnalysis) throw new Error('AI 未返回语音分析结论')
  return {
    emotionVector,
    confidence: Number.isFinite(confidence) ? Math.max(0, Math.min(1, confidence)) : 0.75,
    indicators: {
      isLowSpeed: Boolean(indicators.isLowSpeed ?? indicators.is_low_speed),
      isHighPitchDrop: Boolean(indicators.isHighPitchDrop ?? indicators.is_high_pitch_drop),
      isLongPause: Boolean(indicators.isLongPause ?? indicators.is_long_pause),
    },
    depressionAnalysis,
  }
}

const requestVoiceAiReport = async (text: string, speechMetrics: VoiceReport['speechMetrics']) => {
  const response = await chatCompletion([
    {
      role: 'system',
      content: [
        '你是初心的语音情绪评估助手。',
        '你会基于真实 ASR 转写文本和声学指标进行情绪分析，不得忽略用户文本语义。',
        '必须只返回 JSON，不要 Markdown，不要解释。',
        'JSON schema: {"emotion_vector":{"calm":0,"happy":0,"sad":0,"angry":0,"surprised":0,"fearful":0,"disgusted":0,"neutral":0},"confidence":0.0,"indicators":{"isLowSpeed":false,"isHighPitchDrop":false,"isLongPause":false},"depression_analysis":"30-80字中文结论"}',
        'emotion_vector 8 个数值必须非负，合计接近 1。',
        'emotion_vector 必须随 ASR 文本语义和声学指标变化，不能返回固定模板、平均分布或忽略“开心/难过/紧张”等明确情绪词。',
      ].join('\n'),
    },
    {
      role: 'user',
      content: [
        `ASR转写文本：${text}`,
        `语速：${speechMetrics.speed} 字/分`,
        `语调基频：${speechMetrics.tone} Hz`,
        `停顿时长：${speechMetrics.pause} 秒`,
        `能量值：${speechMetrics.energy} dB`,
      ].join('\n'),
    },
  ])
  return parseVoiceAiResult(extractChatCompletionText(response))
}

const buildVoiceReport = async (text: string, analysisBlob: Blob): Promise<VoiceReport> => {
  const normalizedText = text.trim()
  if (!normalizedText) {
    throw new Error('语音服务未返回转写文本')
  }

  const buffer = await decodeAudioBuffer(analysisBlob)
  const sampleRate = buffer.sampleRate
  const channelData = buffer.getChannelData(0)
  const frameSize = Math.floor(sampleRate * 0.02)
  let rmsSum = 0
  let rmsSqSum = 0
  let frames = 0
  let pauses = 0

  for (let offset = 0; offset < channelData.length; offset += frameSize) {
    const end = Math.min(offset + frameSize, channelData.length)
    let rms = 0
    for (let index = offset; index < end; index += 1) {
      const value = channelData[index] ?? 0
      rms += value * value
    }
    const sampleCount = Math.max(1, end - offset)
    rms = Math.sqrt(rms / sampleCount)
    if (rms < 0.02) pauses += 1
    rmsSum += rms
    rmsSqSum += rms * rms
    frames += 1
  }

  const safeFrames = Math.max(1, frames)
  const avgRms = rmsSum / safeFrames
  const varRms = Math.max(0, rmsSqSum / safeFrames - avgRms * avgRms)
  const durationSec = Math.max(0.1, buffer.duration)
  const pauseRatio = pauses / safeFrames
  const speechRateApprox = normalizedText.length / (durationSec / 60)
  const speechMetrics = {
    speed: speechRateApprox.toFixed(0),
    tone: (avgRms * 1000).toFixed(0),
    pause: (pauses * 0.02).toFixed(1),
    energy: (20 * Math.log10(avgRms + 0.0001) + 100).toFixed(1),
  }
  const aiReport = await requestVoiceAiReport(normalizedText, speechMetrics)

  return {
    text: normalizedText,
    confidence: aiReport.confidence,
    emotionVector: aiReport.emotionVector,
    speechMetrics,
    indicators: aiReport.indicators,
    depressionAnalysis: aiReport.depressionAnalysis,
  }
}

const analyzeAudioBlob = async (blob: Blob | null) => {
  clearVoiceTimers()
  voiceCaptureState.value = 'analyzing'
  voiceAnalysisProgress.value = 8
  statusMessage.value = '正在分析语音情绪特征...'
  errorMessage.value = ''
  voiceProgressTimer = setInterval(() => {
    voiceAnalysisProgress.value = Math.min(95, voiceAnalysisProgress.value + 12)
    refreshWaveform()
  }, 180)

  try {
    let recognizedText = ''
    if (!blob || blob.size <= 0) {
      throw new Error('未采集到有效音频，请录音或上传音频文件')
    }
    const shouldConvertToWav = /webm|ogg|opus/i.test(blob.type || '')
    const analysisBlob = shouldConvertToWav ? await convertWebmToWav(blob) : blob
    const base64 = await blobToBase64(analysisBlob)
    const result = await speechRecognition(base64, inferAudioFormat(analysisBlob), 16000, analysisBlob.size)
    recognizedText = String(result?.text || result?.result?.[0] || '').trim()
    if (!recognizedText) {
      throw new Error('语音服务未返回转写文本')
    }
    voiceReport.value = await buildVoiceReport(recognizedText, analysisBlob)
    voiceRecognizedText.value = voiceReport.value.text
    voiceAnalysisProgress.value = 100
    voiceCaptureState.value = 'done'
    voiceCompleted.value = true
    voiceReportOpen.value = true
    statusMessage.value = '分析完成'
  } catch (error) {
    voiceCaptureState.value = 'idle'
    voiceCompleted.value = false
    voiceReportOpen.value = false
    errorMessage.value = error instanceof Error ? `语音识别失败：${error.message}` : '语音识别失败，请重试'
  } finally {
    clearVoiceTimers()
    stopMicStream()
  }
}

const updateLiveWaveform = () => {
  if (!analyser) {
    refreshWaveform()
    waveformFrame = requestAnimationFrame(updateLiveWaveform)
    return
  }
  const dataArray = new Uint8Array(analyser.frequencyBinCount)
  analyser.getByteFrequencyData(dataArray)
  voiceWaveform.value = Array.from({ length: 50 }, (_, index) => {
    const dataIndex = Math.floor((index / 50) * dataArray.length)
    const value = dataArray[dataIndex] || 0
    return Math.max(8, Math.min(95, 10 + (value / 255) * 85))
  })
  waveformFrame = requestAnimationFrame(updateLiveWaveform)
}

const startVoiceCapture = async () => {
  clearVoiceTimers()
  stopMicStream()
  voiceCaptureState.value = 'recording'
  voiceDuration.value = 0
  voiceAnalysisProgress.value = 0
  voiceFileName.value = ''
  voiceCompleted.value = false
  voiceReportOpen.value = false
  voiceReport.value = null
  voiceRecognizedText.value = ''
  audioChunks = []
  statusMessage.value = '语音采集已启动'
  errorMessage.value = ''

  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw new Error('当前页面无法开启麦克风，请使用 HTTPS 访问或上传音频文件。')
    }
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(micStream)
    try {
      audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(micStream)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
    } catch {
      analyser = null
      void audioContext?.close().catch(() => undefined)
      audioContext = null
    }
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data)
    }
    mediaRecorder.onstop = () => {
      const type = audioChunks[0]?.type || 'audio/webm'
      void analyzeAudioBlob(new Blob(audioChunks, { type }))
    }
    mediaRecorder.start()
    updateLiveWaveform()
  } catch (error) {
    voiceCaptureState.value = 'idle'
    errorMessage.value = error instanceof Error ? error.message : '无法开启麦克风，请检查浏览器权限或改用 HTTPS 访问。'
    clearVoiceTimers()
    stopMicStream()
    return
  }

  voiceTimer = setInterval(() => {
    voiceDuration.value += 1
    if (!analyser) refreshWaveform()
    if (voiceDuration.value >= 10) {
      stopVoiceCapture()
    }
  }, 1000)
}

const stopVoiceCapture = () => {
  if (voiceCaptureState.value !== 'recording') return
  clearVoiceTimers()
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  } else {
    void analyzeAudioBlob(null)
  }
}

const handleVoiceUpload = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = '文件大小不能超过50MB'
    return
  }
  voiceFileName.value = file.name
  voiceDuration.value = 10
  await analyzeAudioBlob(file)
  ;(event.target as HTMLInputElement).value = ''
}

const completeVoice = () => {
  if (voiceCaptureState.value === 'recording') {
    stopVoiceCapture()
    return
  }
  if (voiceCaptureState.value !== 'done') {
    errorMessage.value = '请先完成真实录音或上传音频并等待识别报告生成'
    return
  }
  voiceCompleted.value = true
  voiceReportOpen.value = false
  if (isMobile.value) step.value = 'expression'
}

const clearExpressionTimers = () => {
  if (expressionTimer) {
    clearInterval(expressionTimer)
    expressionTimer = null
  }
  if (expressionProgressTimer) {
    clearInterval(expressionProgressTimer)
    expressionProgressTimer = null
  }
}

const stopExpressionStream = () => {
  if (expressionFpsFrame) {
    cancelAnimationFrame(expressionFpsFrame)
    expressionFpsFrame = 0
  }
  expressionStream?.getTracks().forEach((track) => track.stop())
  expressionStream = null
  if (expressionVideo.value) {
    expressionVideo.value.srcObject = null
  }
}

const updateExpressionFps = () => {
  const now = performance.now()
  if (expressionLastFrameAt > 0) {
    const delta = Math.max(1, now - expressionLastFrameAt)
    expressionFps.value = Math.min(60, Math.max(1, Math.round(1000 / delta)))
  }
  expressionLastFrameAt = now
  if (expressionStream) {
    expressionFpsFrame = requestAnimationFrame(updateExpressionFps)
  }
}

const startExpressionCamera = async () => {
  expressionCameraStarted.value = true
  errorMessage.value = ''
  stopExpressionStream()
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    errorMessage.value = '当前远程 HTTP 页面无法开启摄像头，请使用 HTTPS 访问'
    return
  }
  try {
    expressionStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: expressionFacingMode.value, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    })
    if (expressionVideo.value) {
      expressionVideo.value.srcObject = expressionStream
      await expressionVideo.value.play().catch(() => undefined)
    }
    expressionLastFrameAt = performance.now()
    updateExpressionFps()
  } catch (error) {
    errorMessage.value = error instanceof Error ? `无法启动摄像头：${error.message}` : '无法启动摄像头，请检查浏览器权限或改用 HTTPS 访问'
  }
}

const switchExpressionCamera = async () => {
  expressionFacingMode.value = expressionFacingMode.value === 'user' ? 'environment' : 'user'
  if (expressionCameraStarted.value) {
    await startExpressionCamera()
  }
}

const readExpressionFrameSignals = () => {
  const video = expressionVideo.value
  if (!video || !video.videoWidth || !video.videoHeight) return null
  const canvas = document.createElement('canvas')
  canvas.width = 96
  canvas.height = 72
  const context = canvas.getContext('2d')
  if (!context) return null
  try {
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
  } catch {
    return null
  }
  const { data } = context.getImageData(0, 0, canvas.width, canvas.height)
  const sampleRegion = (x1: number, y1: number, x2: number, y2: number) => {
    let luminanceTotal = 0
    let contrastTotal = 0
    let count = 0
    let previous = 0
    for (let y = y1; y < y2; y += 2) {
      for (let x = x1; x < x2; x += 2) {
        const offset = (y * canvas.width + x) * 4
        const luminance = ((data[offset] ?? 0) * 0.299 + (data[offset + 1] ?? 0) * 0.587 + (data[offset + 2] ?? 0) * 0.114) / 255
        luminanceTotal += luminance
        if (count > 0) contrastTotal += Math.abs(luminance - previous)
        previous = luminance
        count += 1
      }
    }
    return {
      luminance: count > 0 ? luminanceTotal / count : 0,
      contrast: count > 1 ? contrastTotal / (count - 1) : 0,
    }
  }
  const browRegion = sampleRegion(24, 18, 72, 32)
  const eyeRegion = sampleRegion(22, 26, 74, 42)
  const mouthRegion = sampleRegion(28, 44, 68, 60)
  return {
    brow: Math.min(0.85, Math.max(0.12, browRegion.contrast * 2.8 + (1 - browRegion.luminance) * 0.18)),
    mouth: Math.min(0.82, Math.max(0.1, mouthRegion.contrast * 2.4 + (1 - mouthRegion.luminance) * 0.16)),
    blink: Math.min(0.9, Math.max(0.08, (1 - eyeRegion.luminance) * 0.42 + eyeRegion.contrast * 1.8)),
  }
}

const refreshExpressionSignals = () => {
  const nextSignals = readExpressionFrameSignals()
  if (!nextSignals) return false
  const brow = expressionSignals.value.brow * 0.6 + nextSignals.brow * 0.4
  const mouth = expressionSignals.value.mouth * 0.6 + nextSignals.mouth * 0.4
  const blink = expressionSignals.value.blink * 0.6 + nextSignals.blink * 0.4
  expressionSignals.value = { brow, mouth, blink }
  expressionConfidence.value = Math.min(0.91, 0.58 + brow * 0.18 + blink * 0.16)
  return true
}

const getExpressionMicroFeatureText = (feature: keyof ExpressionAiReport['micro_features']) => {
  const fromAi = expressionAiReport.value?.micro_features?.[feature]
  if (fromAi) return fromAi
  return '等待 multimodal-analysis 返回真实微表情特征'
}

const captureExpressionSnapshot = () => {
  const video = expressionVideo.value
  if (!video || !video.videoWidth || !video.videoHeight) return ''
  const canvas = document.createElement('canvas')
  const maxWidth = 320
  const ratio = Math.min(1, maxWidth / video.videoWidth)
  canvas.width = Math.round(video.videoWidth * ratio)
  canvas.height = Math.round(video.videoHeight * ratio)
  if (canvas.width < 120 || canvas.height < 90) return ''
  const context = canvas.getContext('2d')
  if (!context) return ''
  try {
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
  } catch {
    return ''
  }
  const dataUrl = canvas.toDataURL('image/jpeg', 0.6)
  return dataUrl.length > 1000 ? dataUrl : ''
}

const parseExpressionAiResult = (content: string): ExpressionAiReport | null => {
  const jsonText = content.match(/\{[\s\S]*\}/)?.[0]
  if (!jsonText) return null
  try {
    const parsed = JSON.parse(jsonText)
    const radar = parsed?.emotion_radar
    const microFeatures = parsed?.micro_features
    const requiredRadarKeys = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'fearful', 'disgusted', 'contempt', 'pain']
    const hasValidRadar = radar && requiredRadarKeys.every((key) => typeof radar[key] === 'number')
    const hasValidRisk = typeof parsed?.depression_risk_score === 'number'
    const hasValidReport = String(parsed?.analysis_report || '').trim().length > 0
    const hasValidMicroFeatures = Boolean(
      microFeatures &&
        String(microFeatures.brow_furrow || '').trim() &&
        String(microFeatures.mouth_droop || '').trim() &&
        String(microFeatures.eye_contact || '').trim(),
    )
    if (!hasValidRadar || !hasValidRisk || !hasValidReport || !hasValidMicroFeatures) return null
    const report: ExpressionAiReport = {
      emotion_radar: parsed.emotion_radar,
      depression_risk_score: Number(parsed.depression_risk_score),
      analysis_report: String(parsed.analysis_report),
      micro_features: {
        brow_furrow: String(microFeatures.brow_furrow),
        mouth_droop: String(microFeatures.mouth_droop),
        eye_contact: String(microFeatures.eye_contact),
      },
    }
    return report
  } catch {
    return null
  }
}

const analyzeExpressionSnapshot = async () => {
  const snapshot = captureExpressionSnapshot()
  expressionSnapshot.value = snapshot
  if (!snapshot) {
    throw new Error('无法捕获面部图像，请确认摄像头已开启且面部清晰可见')
  }

  try {
    const prompt = `分析面部图像，返回JSON格式：
{
  "emotion_radar": {"neutral":0.4,"happy":0.1,"sad":0.3,"angry":0.05,"surprised":0.05,"fearful":0.05,"disgusted":0.02,"contempt":0.02,"pain":0.01},
  "depression_risk_score": 65,
  "analysis_report": "面部特征分析摘要，30字以内",
  "micro_features": {
    "brow_furrow": "眉心状态描述，15字以内",
    "mouth_droop": "嘴角状态描述，15字以内",
    "eye_contact": "眼神状态描述，15字以内"
  }
}`
    const response = await multimodalAnalysis([
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: snapshot } },
        ],
      },
    ])
    const content = String(response?.choices?.[0]?.message?.content || response?.text || '')
    const parsedReport = parseExpressionAiResult(content)
    if (!parsedReport) {
      throw new Error('多模态视觉服务未返回有效表情报告')
    }
    expressionAiReport.value = parsedReport
  } catch (error) {
    const message = error instanceof Error ? error.message : '多模态视觉服务暂时不可用'
    throw new Error(message)
  }
}

const finishExpressionAnalysis = async () => {
  clearExpressionTimers()
  refreshExpressionSignals()
  try {
    await analyzeExpressionSnapshot()
  } catch (error) {
    expressionAiReport.value = null
    expressionStatus.value = 'idle'
    expressionProgress.value = 0
    expressionCompleted.value = false
    expressionReportOpen.value = false
    errorMessage.value = error instanceof Error ? `面部识别失败：${error.message}` : '面部识别失败，请重试'
    return
  }
  const dominant = expressionRadarItems.value.reduce((max, item) => (item.value > max.value ? item : max), expressionRadarItems.value[0]!)
  expressionDominantEmotion.value = dominant.label
  expressionConfidence.value = Math.min(0.95, 0.62 + dominant.value * 0.3)
  expressionProgress.value = 100
  expressionStatus.value = 'completed'
  expressionCompleted.value = true
  expressionReportOpen.value = true
  stopExpressionStream()
}

const startExpressionCapture = async () => {
  if (!expressionCameraStarted.value || !expressionStream) {
    await startExpressionCamera()
    if (!expressionStream) return
  }
  clearExpressionTimers()
  expressionStatus.value = 'capturing'
  expressionCountdown.value = 5
  expressionProgress.value = 0
  expressionNoFaceCount.value = 0
  expressionReportOpen.value = false
  expressionCompleted.value = false
  expressionAiReport.value = null
  expressionSnapshot.value = ''
  errorMessage.value = ''
  expressionTimer = setInterval(() => {
    const hasFrameSignal = refreshExpressionSignals()
    expressionNoFaceCount.value = hasFrameSignal ? 0 : expressionNoFaceCount.value + 1
    expressionCountdown.value -= 1
    if (expressionCountdown.value <= 0) {
      expressionStatus.value = 'analyzing'
      expressionProgressTimer = setInterval(() => {
        expressionProgress.value = Math.min(100, expressionProgress.value + 14)
        if (expressionProgress.value >= 100) {
          void finishExpressionAnalysis()
        }
      }, 140)
      clearInterval(expressionTimer!)
      expressionTimer = null
    }
  }, 500)
}

const completeExpression = async () => {
  if (!expressionCameraStarted.value) {
    void startExpressionCamera()
    return
  }
  if (expressionStatus.value === 'idle') {
    void startExpressionCapture()
    return
  }
  if (expressionStatus.value === 'analyzing') {
    errorMessage.value = '视觉模型正在分析中，请稍候'
    return
  }
  if (expressionStatus.value !== 'completed') {
    void finishExpressionAnalysis()
    return
  }
  expressionReportOpen.value = false
  if (!allCompleted.value) {
    statusMessage.value = '表情识别已完成，请继续完成对话评估和语音情绪识别后生成多模态评估报告'
    errorMessage.value = ''
    return
  }
  await buildReport()
}

const openHtp = () => {
  router.push('/assessment/htp')
}

const loadMultimodalTaskState = async () => {
  if (!authState.user) return
  try {
    publishTasks.value = await getMyAssessmentPublishTasks()
  } catch {
    publishTasks.value = []
  }
}

const moduleWarning = (score: number) => {
  if (score >= 75) return 'high'
  if (score >= 55) return 'middle'
  if (score >= 35) return 'low'
  return 'none'
}

const syncMultimodalTaskResults = async (
  voiceData: Record<string, unknown>,
  expressionData: ExpressionAiReport,
  fusionPayload: ReturnType<typeof extractFusionPayload>,
) => {
  if (!multimodalTaskItems.value.length || !scaleResult.value) return
  taskSyncing.value = true
  taskSyncDone.value = false
  const scaleNormalized = calculateScaleNormalized(scaleRawScore.value)
  const payloadByType: Record<string, Record<string, unknown>> = {
    dialogue_scale: {
      rawData: {
        scaleTypes: scaleResult.value.scaleTypes,
        conversationHistory: scaleResult.value.conversationHistory,
        summary: scaleSummary.value.summary,
      },
      metrics: { score: scaleNormalized, rawScore: scaleRawScore.value },
      report: {
        title: '对话式心理健康评估',
        moduleType: 'dialogue_scale',
        summary: scaleSummary.value.summary,
        score: scaleNormalized,
        riskLevel: moduleWarning(scaleNormalized),
        warningLevel: moduleWarning(scaleNormalized),
        feedbackCards: [{
          title: '结果反馈',
          level: moduleWarning(scaleNormalized),
          conclusion: scaleSummary.value.summary,
          suggestion: '请结合语音、表情和量表结果综合查看。',
        }],
      },
    },
    voice: {
      rawData: voiceData,
      metrics: { score: voiceScore.value },
      report: {
        title: '语音识别',
        moduleType: 'voice',
        summary: voiceSummary.value.summary,
        score: voiceScore.value,
        riskLevel: moduleWarning(voiceScore.value),
        warningLevel: moduleWarning(voiceScore.value),
        feedbackCards: [{
          title: '结果反馈',
          level: moduleWarning(voiceScore.value),
          conclusion: voiceSummary.value.summary,
          suggestion: '请结合对话和表情结果复核语音线索。',
        }],
      },
    },
    expression: {
      rawData: { ...expressionData, snapshotCaptured: Boolean(expressionSnapshot.value) },
      metrics: { score: expressionScore.value },
      report: {
        title: '表情评估',
        moduleType: 'expression',
        summary: expressionSummary.value.summary,
        score: expressionScore.value,
        riskLevel: moduleWarning(expressionScore.value),
        warningLevel: moduleWarning(expressionScore.value),
        feedbackCards: [{
          title: '结果反馈',
          level: moduleWarning(expressionScore.value),
          conclusion: expressionSummary.value.summary,
          suggestion: '请结合对话和语音结果复核面部情绪线索。',
        }],
      },
    },
  }
  try {
    for (const item of multimodalTaskItems.value) {
      const payload = payloadByType[item.item_type]
      if (payload) {
        await submitAssessmentTaskModuleItem(item.id, {
          ...payload,
          fusionSummary: fusionPayload.detailedReport,
        })
      }
    }
    taskSyncDone.value = true
    await loadMultimodalTaskState()
  } finally {
    taskSyncing.value = false
  }
}

const buildReport = async () => {
  if (!allCompleted.value) return
  statusMessage.value = ''
  errorMessage.value = ''
  taskSyncDone.value = false
  if (!scaleResult.value || !voiceReport.value || !expressionAiReport.value) {
    errorMessage.value = '评估原始结果不完整，不能生成AI多模态报告。请完成真实量表、语音识别和面部识别流程。'
    return
  }
  const scaleNormalized = calculateScaleNormalized(scaleRawScore.value)
  const localWeightedScore = Math.round(scaleNormalized * 0.5 + voiceScore.value * 0.2 + expressionScore.value * 0.3)
  const voiceData = {
    score: voiceScore.value,
    risk_score: voiceScore.value,
    emotion_score: voiceScore.value,
    text: voiceReport.value.text,
    emotion_vector: voiceReport.value.emotionVector,
    emotions: voiceReport.value.emotionVector,
    speech_metrics: voiceReport.value.speechMetrics,
    indicators: voiceReport.value.indicators,
    analysis: voiceReport.value.depressionAnalysis,
    depression_analysis: voiceReport.value.depressionAnalysis,
  }
  let fusionPayload: ReturnType<typeof extractFusionPayload>
  try {
    statusMessage.value = '正在生成AI多模态报告...'
    const response = await multimodalFusion({
      user_id: state.currentAccountId || '',
      assessment_id: `assessment-${Date.now()}`,
      text_analysis: {
        ...scaleResult.value,
        normalized_score: scaleNormalized,
      },
      voice_analysis: voiceData,
      video_analysis: expressionAiReport.value,
      image_analysis: expressionAiReport.value,
    })
    fusionPayload = extractFusionPayload(response)
  } catch (error) {
    errorMessage.value = error instanceof Error ? `AI多模态报告生成失败：${error.message}` : 'AI多模态报告生成失败，请稍后重试'
    statusMessage.value = ''
    return
  }
  const overallScore = fusionPayload.score
  const nextReport = {
    scale: scaleSummary.value,
    voice: voiceSummary.value,
    expression: expressionSummary.value,
    overall: {
      score: overallScore,
      label: overallScore >= 75 ? '建议尽快跟进' : overallScore >= 55 ? '建议持续观察' : '当前波动较低',
      summary: fusionPayload.detailedReport,
    },
  }
  const generatedAt = new Date().toLocaleString('zh-CN')
  try {
    await addAssessment({
    id: `assessment-${Date.now()}`,
    createdAt: generatedAt,
    report: {
      scaleData: scaleResult.value,
      voiceData,
      expressionData: expressionAiReport.value,
      weights: { scale: 0.5, voice: 0.2, expression: 0.3 },
      advice: fusionPayload.recommendations.length > 0
        ? fusionPayload.recommendations.map((item: string, index: number) => `${index + 1}. ${item}`).join('\n')
        : fusionPayload.detailedReport,
      fusionAi: fusionPayload,
      localWeightedScore,
    },
    ...nextReport,
  })
  } catch (error) {
    errorMessage.value = error instanceof Error ? `AI多模态报告同步失败：${error.message}` : 'AI多模态报告同步失败，请重试'
    return
  }
  try {
    await syncMultimodalTaskResults(voiceData, expressionAiReport.value, fusionPayload)
  } catch (error) {
    errorMessage.value = error instanceof Error ? `任务结果回写失败：${error.message}` : '任务结果回写失败，请稍后在任务中心检查'
    return
  }
  report.value = nextReport
  reportGeneratedAt.value = generatedAt
  reportAdvice.value = fusionPayload.recommendations.length > 0
    ? fusionPayload.recommendations.map((item: string, index: number) => `${index + 1}. ${item}`).join('\n')
    : fusionPayload.detailedReport
  statusMessage.value = taskSyncDone.value ? '报告已同步至云端，并已回写测评任务' : '报告已同步至云端'
  step.value = 'report'
}

const closeFusionReport = () => {
  void router.push('/profile')
}

onMounted(() => {
  scaleResumeBanner.value = !!loadScaleSession()
  void loadMultimodalTaskState()
})

watch(
  () => state.currentAccountId,
  () => {
    if (!scaleStarted.value && !scaleCompleted.value) {
      scaleResumeBanner.value = !!loadScaleSession()
    }
  },
)

watch(
  [scaleMessages, scaleQuestionIndex, selectedScales],
  () => {
    saveScaleSession()
  },
  { deep: true },
)

watch(toastMessage, (message) => {
  if (toastTimer) clearTimeout(toastTimer)
  if (!message) return
  toastTimer = setTimeout(() => {
    statusMessage.value = ''
    errorMessage.value = ''
  }, errorMessage.value ? 4200 : 2400)
})

onBeforeUnmount(() => {
  clearScaleTyping()
  clearScaleReadTimer()
  stopScaleVoiceInput()
  stopScaleVoiceStream()
  clearVoiceTimers()
  stopMicStream()
  clearExpressionTimers()
  stopExpressionStream()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-100 dark:bg-slate-950">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-5 z-[90] w-[calc(100%-32px)] max-w-sm -translate-x-1/2 rounded-xl border px-4 py-3 text-sm font-medium shadow-xl backdrop-blur"
      :class="toastTone === 'error' ? 'border-amber-200 bg-white text-amber-800' : 'border-slate-200 bg-white text-slate-800'"
      data-testid="assessment-toast"
    >
      {{ toastMessage }}
    </div>

    <div v-if="step === 'report' && report" class="min-h-screen bg-slate-50 pb-10 dark:bg-slate-950">
      <div class="sticky top-0 z-40 border-b border-slate-100 bg-white px-4 py-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div class="mx-auto flex max-w-md items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <button
              class="-ml-2 inline-flex h-10 w-10 items-center justify-center rounded-full text-slate-900 hover:bg-slate-100 dark:text-white dark:hover:bg-slate-800"
              aria-label="关闭报告"
              data-testid="fusion-close"
              @click="closeFusionReport"
            >
              <X class="h-6 w-6" />
            </button>
            <h1 class="text-xl font-bold leading-tight text-slate-900 dark:text-white">AI多模态报告</h1>
          </div>
          <div class="flex items-center gap-2">
            <button class="inline-flex h-9 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200" data-testid="fusion-history-trigger" @click="openFusionHistory">
              <Clock class="h-4 w-4" />
              历史记录
            </button>
            <button class="inline-flex h-9 items-center gap-2 rounded-full bg-[#1E6EFF] px-4 text-xs font-bold text-white shadow-lg shadow-blue-500/20" data-testid="fusion-export-pdf" @click="exportFusionReport('pdf')">
              <Download class="h-4 w-4" />
              导出PDF
            </button>
          </div>
        </div>
      </div>

      <div class="mx-auto mt-4 max-w-md px-4">
        <p class="text-sm text-slate-500">根据量表、语音和表情三个模块生成每日 AI 多模态报告；它不同于任务中心的一次性职务犯罪初筛总报告。</p>
      </div>

      <div class="mx-auto max-w-md px-4">
      <div ref="fusionReportEl" class="mt-6">
        <BaseCard class="overflow-hidden border-0 bg-white shadow-xl shadow-slate-200/60 dark:bg-slate-900 dark:shadow-none">
          <div class="h-2 bg-[#10B981]" />
          <div class="p-6">
          <div class="grid grid-cols-3 gap-2">
            <button class="h-10 rounded-[10px] bg-gradient-to-r from-blue-500 to-blue-600 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-blue-500/20" data-testid="fusion-open-scale" @click="activeReport = 'scale'">对话评估报告</button>
            <button class="h-10 rounded-[10px] bg-gradient-to-r from-violet-500 to-purple-600 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-violet-500/20" data-testid="fusion-open-voice" @click="activeReport = 'voice'">语音情绪报告</button>
            <button class="h-10 rounded-[10px] bg-gradient-to-r from-cyan-500 to-teal-500 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-cyan-500/20" data-testid="fusion-open-expression" @click="activeReport = 'expression'">表情识别报告</button>
          </div>

          <div class="mt-6 border-t border-slate-100 pt-6 dark:border-slate-800">
            <div class="grid gap-3 md:grid-cols-3">
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">综合风险分</p>
                <p class="mt-2 text-3xl font-black" :class="fusionRiskLevel === 'high' || fusionRiskLevel === 'extreme' ? 'text-rose-500' : 'text-emerald-500'" data-testid="fusion-score">{{ report.overall.score }}</p>
                <p class="mt-1 text-[10px] text-slate-400">满分 100</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">风险等级</p>
                <span class="mt-3 inline-flex rounded-full px-3 py-1 text-xs font-bold text-white" :class="riskBadgeClass" data-testid="fusion-risk-badge">{{ riskTextMap[fusionRiskLevel] }}</span>
              </div>
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">主要影响因子</p>
                <p class="mt-3 text-base font-bold text-slate-800 dark:text-white">量表</p>
                <p class="mt-1 text-[10px] text-slate-400">权重 50%</p>
              </div>
            </div>

            <div class="mt-5 rounded-xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200">
                <Activity class="h-4 w-4 text-emerald-500" />
                多维度得分详情
              </h3>
              <div class="mt-4 space-y-4">
                <div>
                  <div class="flex items-center justify-between">
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><FileText class="h-4 w-4 text-blue-600" />对话评估 (50%)</span>
                    <span class="font-bold">{{ scaleRawScore }} <span class="text-xs text-slate-400">/ 27</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-blue-500" :style="{ width: `${Math.min(100, (scaleRawScore / 27) * 100)}%` }" /></div>
                </div>
                <div>
                  <div class="flex items-center justify-between">
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><Mic class="h-4 w-4 text-violet-600" />语音情绪 (20%)</span>
                    <span class="font-bold">{{ voiceScore }} <span class="text-xs text-slate-400">/ 100</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-violet-500" :style="{ width: `${voiceScore}%` }" /></div>
                </div>
                <div>
                  <div class="flex items-center justify-between">
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><Video class="h-4 w-4 text-cyan-600" />表情识别 (30%)</span>
                    <span class="font-bold">{{ expressionScore }} <span class="text-xs text-slate-400">/ 100</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-cyan-500" :style="{ width: `${expressionScore}%` }" /></div>
                </div>
              </div>
            </div>

            <div class="mt-5 grid gap-3 md:grid-cols-2">
              <div class="rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 p-4 dark:border-blue-950 dark:from-blue-950/30 dark:to-indigo-950/30">
                <h3 class="flex items-center gap-2 text-sm font-bold text-blue-800 dark:text-blue-200"><Heart class="h-4 w-4" />心理调节建议</h3>
                <ul class="mt-3 space-y-2 text-xs leading-5 text-slate-700 dark:text-slate-200">
                  <li>每天进行10分钟正念冥想练习</li>
                  <li>保持规律作息，确保7-8小时睡眠</li>
                  <li>适度运动，每周3次有氧运动</li>
                </ul>
              </div>
              <div class="rounded-xl border border-amber-100 bg-gradient-to-br from-amber-50 to-orange-50 p-4 dark:border-amber-950 dark:from-amber-950/30 dark:to-orange-950/30">
                <h3 class="flex items-center gap-2 text-sm font-bold text-amber-800 dark:text-amber-200"><Stethoscope class="h-4 w-4" />专业干预建议</h3>
                <ul class="mt-3 space-y-2 text-xs leading-5 text-slate-700 dark:text-slate-200">
                  <li>建议预约心理咨询师进行深度评估</li>
                  <li>考虑认知行为疗法（CBT）干预</li>
                  <li>定期复查，建议2周后重新评估</li>
                </ul>
              </div>
            </div>

            <div class="mt-5 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 p-4 dark:border-emerald-950 dark:from-emerald-950/30 dark:via-teal-950/30 dark:to-cyan-950/30" data-testid="fusion-professional-advice">
              <h3 class="flex items-center gap-2 font-bold text-emerald-800 dark:text-emerald-200"><Lightbulb class="h-5 w-5" />智能诊断结论</h3>
              <p class="mt-3 whitespace-pre-line rounded-lg bg-white/70 p-3 text-sm leading-7 text-slate-700 dark:bg-slate-950/40 dark:text-slate-200">{{ professionalAdvice }}</p>
            </div>
          </div>
          </div>
        </BaseCard>
      </div>
      </div>

      <div v-if="fusionHistoryOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="fusion-history-dialog">
        <section class="flex max-h-[86vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl bg-white p-5 shadow-xl dark:bg-slate-950">
          <div class="flex shrink-0 items-center justify-between">
            <h2 class="text-xl font-black text-slate-900 dark:text-white">历史记录</h2>
            <button class="grid h-9 w-9 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="fusion-history-close" @click="fusionHistoryOpen = false"><X class="h-5 w-5 text-slate-400" /></button>
          </div>
          <div class="mt-4 space-y-2 overflow-y-auto pr-1">
            <div v-if="fusionHistoryLoading" class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900" data-testid="fusion-history-loading">
              正在加载历史记录...
            </div>
            <button
              v-else
              v-for="item in state.assessments.slice(0, 10)"
              :key="item.id"
              class="w-full rounded-xl border border-slate-100 bg-slate-50 p-3 text-left text-sm transition hover:border-primary/40 hover:bg-primary/5 dark:border-slate-800 dark:bg-slate-900"
              data-testid="fusion-history-item"
              @click="loadFusionHistoryItem(item)"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-bold text-slate-800 dark:text-white">{{ item.createdAt }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ item.overall.label }}</p>
                </div>
                <span class="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{{ item.overall.score }}</span>
              </div>
            </button>
            <p v-if="!fusionHistoryLoading && state.assessments.length === 0" class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900">暂无历史记录</p>
          </div>
        </section>
      </div>

      <BaseCard class="mt-6">
        <SectionTitle title="最近评估记录" description="回顾近期评估结果，持续观察心理状态变化。" />
        <div class="mt-4 space-y-3">
          <div
            v-for="item in state.assessments.slice(0, 5)"
            :key="item.id"
            class="rounded-[24px] border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-slate-900 dark:text-white">{{ item.createdAt }}</p>
                <p class="text-sm text-slate-500">{{ item.overall.label }}</p>
              </div>
              <span class="rounded-full bg-primary/10 px-3 py-2 text-sm font-semibold text-primary">{{ item.overall.score }}</span>
            </div>
          </div>
        </div>
      </BaseCard>

      <div v-if="activeReport" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="fusion-subreport-dialog">
        <section class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[20px] bg-white shadow-xl dark:bg-slate-950">
          <header
            class="flex items-center justify-between px-5 py-4 text-white"
            :class="activeReport === 'scale' ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600' : activeReport === 'voice' ? 'bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600' : 'bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600'"
          >
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
                <FileText v-if="activeReport === 'scale'" class="h-5 w-5" />
                <Mic v-else-if="activeReport === 'voice'" class="h-5 w-5" />
                <Video v-else class="h-5 w-5" />
              </div>
              <div>
                <h2 class="text-xl font-bold">{{ activeReport === 'scale' ? '对话评估报告' : activeReport === 'voice' ? '语音情绪报告' : '表情识别报告' }}</h2>
                <p class="text-xs text-white/80">{{ activeReport === 'scale' ? 'PHQ-9 抑郁症筛查量表详细得分与分析' : activeReport === 'voice' ? '基于声学特征的情绪状态分析' : '基于面部微表情的情绪状态分析' }}</p>
              </div>
            </div>
            <button @click="activeReport = null"><X class="h-5 w-5" /></button>
          </header>

          <div v-if="activeReport === 'scale'" class="space-y-5 p-5" data-testid="fusion-scale-report-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-600 dark:text-slate-300">PHQ-9 总分</span>
                <span class="rounded-full px-3 py-1 text-xs font-bold text-white" :class="riskBadgeClass">{{ riskTextMap[fusionRiskLevel] }}</span>
              </div>
              <p class="mt-3 text-4xl font-black text-slate-900 dark:text-white">{{ scaleRawScore }} <span class="text-lg text-slate-400">/ 27</span></p>
              <p class="mt-3 text-sm leading-6 text-slate-500">根据您的量表回答，您的抑郁倾向处于{{ riskTextMap[fusionRiskLevel] }}水平。</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-blue-500" />各维度得分详情</h3>
              <div class="mt-4 grid grid-cols-3 gap-3">
                <div v-for="item in scaleResult?.dimensionScores || []" :key="item.label" class="rounded-lg border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
                  <p class="text-xs text-slate-500">{{ item.label }}</p>
                  <p class="mt-1 text-lg font-bold" :class="item.score >= 2 ? 'text-amber-500' : item.score >= 1 ? 'text-blue-500' : 'text-emerald-500'">{{ item.score }} <span class="text-xs text-slate-400">/ {{ item.max }}</span></p>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportFusionReport('pdf')">
                <Download class="mr-2 inline h-4 w-4" />
                导出报告
              </button>
              <button class="rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" @click="activeReport = null">
                关闭
              </button>
            </div>
          </div>

          <div v-else-if="activeReport === 'voice'" class="space-y-5 p-5" data-testid="fusion-voice-report-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-600 dark:text-slate-300">情绪分值</span>
                <span class="rounded-full bg-violet-500 px-3 py-1 text-xs font-bold text-white">{{ voiceScore > 60 ? '波动较大' : '相对平稳' }}</span>
              </div>
              <p class="mt-3 text-4xl font-black text-slate-900 dark:text-white">{{ voiceScore }} <span class="text-lg text-slate-400">/ 100</span></p>
              <p class="mt-3 text-sm leading-6 text-slate-500">{{ voiceSummary.summary }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-violet-500" />声学特征指标</h3>
              <div class="mt-4 grid grid-cols-2 gap-3">
                <div v-for="item in [
                  { label: '语速', value: voiceReport?.speechMetrics.speed || '-', unit: '字/分' },
                  { label: '语调基频', value: voiceReport?.speechMetrics.tone || '-', unit: 'Hz' },
                  { label: '停顿时长', value: voiceReport?.speechMetrics.pause || '-', unit: '秒' },
                  { label: '能量值', value: voiceReport?.speechMetrics.energy || '-', unit: 'dB' },
                ]" :key="item.label" class="rounded-lg border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
                  <p class="text-xs text-slate-500">{{ item.label }}</p>
                  <p class="mt-1 text-lg font-bold text-slate-800 dark:text-white">{{ item.value }} <span class="text-xs text-slate-400">{{ item.unit }}</span></p>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportFusionReport('pdf')">
                <Download class="mr-2 inline h-4 w-4" />
                导出报告
              </button>
              <button class="rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" @click="activeReport = null">
                关闭
              </button>
            </div>
          </div>

          <div v-else class="space-y-5 p-5" data-testid="fusion-expression-report-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-600 dark:text-slate-300">抑郁风险分值</span>
                <span class="rounded-full px-3 py-1 text-xs font-bold text-white" :class="expressionScore > 60 ? 'bg-rose-500' : 'bg-emerald-500'">{{ expressionScore > 60 ? '风险较高' : '风险较低' }}</span>
              </div>
              <p class="mt-3 text-4xl font-black text-slate-900 dark:text-white">{{ expressionScore }} <span class="text-lg text-slate-400">/ 100</span></p>
              <p class="mt-3 text-sm leading-6 text-slate-500">{{ expressionSummary.summary }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-cyan-500" />面部表情分布</h3>
              <div class="mt-4 space-y-3">
                <div v-for="item in expressionRadarItems" :key="item.label" class="flex items-center gap-3">
                  <span class="w-12 text-sm text-slate-600 dark:text-slate-300">{{ item.label }}</span>
                  <div class="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full" :class="item.tone" :style="{ width: `${Math.round(item.value * 100)}%` }" /></div>
                  <span class="w-10 text-right text-sm font-bold text-slate-700 dark:text-slate-200">{{ Math.round(item.value * 100) }}%</span>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportFusionReport('pdf')">
                <Download class="mr-2 inline h-4 w-4" />
                导出报告
              </button>
              <button class="rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" @click="activeReport = null">
                关闭
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div v-else class="flex min-h-[calc(100vh-5rem)] flex-col bg-slate-50 dark:bg-slate-950">
      <div
        v-if="isMobile"
        class="shrink-0 border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900"
        data-testid="assessment-step-navigation"
      >
        <div class="relative mx-auto flex max-w-md items-center justify-between">
          <div class="absolute left-8 right-8 top-5 h-0.5 -translate-y-1/2 bg-slate-100 dark:bg-slate-700" />
          <div class="absolute left-8 top-5 h-0.5 -translate-y-1/2 bg-primary transition-all duration-300" :style="{ width: mobileStepTrackWidth }" />
          <div v-for="item in steps" :key="item.id" class="relative z-10 flex flex-col items-center gap-2">
            <button
              class="relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition"
              :class="step === item.id ? 'border-primary bg-primary text-white shadow-lg shadow-primary/30' : item.done.value || currentStepIndex > steps.findIndex((candidate) => candidate.id === item.id) ? 'border-primary bg-primary/10 text-primary' : 'border-slate-200 bg-white text-slate-400 dark:border-slate-600 dark:bg-slate-800'"
              :aria-label="item.label"
              :data-testid="`assessment-step-${item.id}`"
              @click="step = item.id"
            >
              <Check v-if="item.done.value" class="h-5 w-5" />
              <component :is="item.icon" v-else class="h-5 w-5" />
              <span v-if="step === item.id" class="absolute -inset-1.5 rounded-full border-2 border-primary/40" />
            </button>
            <span class="whitespace-nowrap text-[11px] font-bold" :class="step === item.id ? 'text-primary' : 'text-slate-400'">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <div v-else class="shrink-0 border-b border-slate-200 bg-white px-5 py-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white">
              <Brain class="h-5 w-5" />
            </div>
            <div>
              <h1 class="text-base font-black text-slate-900 dark:text-white">AI 多模态心理评估</h1>
              <p class="text-[11px] text-slate-400">
                {{ multimodalTaskMode ? `待完成任务：${activeMultimodalTaskTitle}，报告会回写任务结果` : '自由测评：可每日完成，生成AI多模态报告' }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1.5 dark:bg-slate-800">
              <Activity class="h-3.5 w-3.5 text-primary" />
              <span class="text-xs font-bold text-slate-600 dark:text-slate-300">{{ completedCount }} / 3 完成</span>
            </div>
            <button
              class="h-9 rounded-xl bg-primary px-5 text-sm font-bold text-white shadow-md shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="!allCompleted || taskSyncing"
              data-testid="generate-fusion-report"
              @click="buildReport"
            >
              {{ taskSyncing ? '同步任务中' : '生成多模态评估报告' }}
            </button>
          </div>
        </div>
      </div>

      <div
        class="w-full flex-1"
        :class="isMobile ? 'relative overflow-hidden' : 'mx-auto grid max-w-7xl gap-4 p-5 lg:grid-cols-3'"
      >
        <BaseCard v-show="!isMobile || step === 'scale'" class="flex h-full flex-col overflow-hidden" :class="isMobile ? 'rounded-none border-0 shadow-none' : ''" :padded="false">
          <div class="flex items-center gap-2 border-b border-slate-100 bg-gradient-to-r from-violet-50 to-indigo-50 px-5 py-3 dark:border-slate-800 dark:from-violet-950/30 dark:to-indigo-950/30">
            <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 text-white">
              <ClipboardList class="h-4 w-4" />
            </div>
            <span class="text-sm font-bold text-slate-800 dark:text-slate-100">对话评估</span>
            <span :class="['ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ring-1', moduleStatusBadgeClass(scaleCompleted)]">
              {{ moduleStatusBadgeText(scaleCompleted) }}
            </span>
          </div>

          <div class="space-y-4 p-5">
            <div class="flex items-start justify-between gap-3">
              <SectionTitle title="AI对话式心理评估" description="您可以选择一个或多个量表进行综合评估。" />
              <button
                class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:border-primary/30 hover:text-primary dark:border-slate-800 dark:bg-slate-900"
                aria-label="查看历史评估"
                data-testid="scale-history-trigger"
                @click="scaleHistoryOpen = true"
              >
                <History class="h-5 w-5" />
              </button>
            </div>
            <div
              v-if="scaleResumeBanner && !scaleStarted"
              class="flex items-center gap-3 rounded-2xl border border-primary/20 bg-primary/5 p-4"
              data-testid="scale-resume-banner"
            >
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <RotateCcw class="h-4 w-4" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">发现未完成的评估</p>
                <p class="mt-0.5 text-xs text-slate-500">上次评估尚未完成，是否继续？</p>
              </div>
              <div class="flex shrink-0 gap-2">
                <button
                  class="h-8 rounded-xl bg-primary px-3 text-xs font-bold text-white shadow-md shadow-primary/20"
                  data-testid="scale-resume-continue"
                  @click="resumeScaleSession"
                >
                  继续
                </button>
                <button
                  class="h-8 rounded-xl px-3 text-xs font-bold text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-900"
                  data-testid="scale-resume-dismiss"
                  @click="clearScaleSession"
                >
                  忽略
                </button>
              </div>
            </div>
            <div v-if="!scaleStarted" class="grid gap-3">
              <button
                v-for="item in scaleCards"
                :key="item.id"
                class="rounded-[16px] border p-4 text-left transition"
                :class="selectedScales.includes(item.id) ? 'border-primary bg-primary/5' : 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900'"
                @click="toggleScale(item.id)"
              >
                <div class="flex items-start justify-between gap-3">
                  <p class="font-semibold text-slate-900 dark:text-white">{{ item.title }}</p>
                  <span v-if="selectedScales.includes(item.id)" class="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white">
                    <Check class="h-4 w-4" />
                  </span>
                </div>
                <p class="mt-1 text-sm text-slate-500">{{ item.subtitle }}</p>
                <p class="mt-2 text-xs text-slate-400">{{ item.questions }} 题 · {{ item.duration }}</p>
              </button>
            </div>

            <button
              v-if="!scaleStarted"
              class="w-full rounded-[12px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
              data-testid="start-scale-assessment"
              @click="startScaleAssessment"
            >
              开始评估
            </button>

            <div v-else class="overflow-hidden rounded-[16px] border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
              <div class="border-b border-slate-100 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-950">
                <div class="flex items-end justify-between">
                  <span class="text-[11px] font-bold uppercase text-slate-400">Progress</span>
                  <span class="text-sm font-black text-primary">{{ Math.min(scaleQuestionIndex, scaleTotalQuestions) }} / {{ scaleTotalQuestions }}</span>
                </div>
                <ProgressBar class="mt-2" :value="(Math.min(scaleQuestionIndex, scaleTotalQuestions) / scaleTotalQuestions) * 100" />
              </div>

              <div ref="scaleMessagesEl" class="max-h-[360px] space-y-4 overflow-y-auto p-4" data-testid="scale-dialogue">
                <div
                  v-for="(message, index) in scaleMessages"
                  :key="`${message.timestamp.toISOString()}-${index}`"
                  class="flex gap-2"
                  :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
                >
                  <div v-if="message.role === 'assistant'" class="h-9 w-9 shrink-0 overflow-hidden rounded-full border-2 border-slate-100 bg-gradient-to-br from-blue-500 to-indigo-500 dark:border-slate-800">
                    <img :src="doctorAvatarUrl" alt="管理员头像" class="h-full w-full object-cover" />
                  </div>
                  <div
                    class="max-w-[72%] rounded-3xl px-4 py-3 text-sm leading-6 shadow-sm"
                    :class="message.role === 'user' ? 'rounded-tr-none bg-primary text-white' : 'rounded-tl-none border border-slate-100 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200'"
                  >
                    {{ scaleTypingMessageIndex === index ? scaleTypingText : message.content }}
                    <span v-if="scaleTypingMessageIndex === index" class="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-slate-400 align-middle" />
                  </div>
                  <div v-if="message.role === 'user'" class="h-9 w-9 shrink-0 overflow-hidden rounded-full border-2 border-primary/20">
                    <img v-if="userAvatarSource.imageUrl" :src="userAvatarSource.imageUrl" alt="用户头像" class="h-full w-full object-cover" />
                    <span v-else :class="['flex h-full w-full items-center justify-center text-sm font-bold', userAvatarSource.preset?.bg || 'bg-gradient-to-br from-primary to-primary/80 text-white']">
                      {{ userAvatarSource.preset?.emoji || userInitial }}
                    </span>
                  </div>
                </div>
                <div v-if="scaleLoading && scaleTypingMessageIndex === null" class="flex justify-start gap-2" data-testid="scale-loading-dots">
                  <div class="h-9 w-9 shrink-0 overflow-hidden rounded-full border-2 border-slate-100 bg-gradient-to-br from-blue-500 to-indigo-500 dark:border-slate-800">
                    <img :src="doctorAvatarUrl" alt="管理员头像" class="h-full w-full object-cover" />
                  </div>
                  <div class="rounded-3xl rounded-tl-none border border-slate-100 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <div class="flex gap-1">
                      <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:0s]" />
                      <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:0.2s]" />
                      <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:0.4s]" />
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="!scaleCompleted" class="space-y-3 border-t border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                <div
                  v-if="scaleEmojiPickerOpen"
                  class="max-h-48 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-800 dark:bg-slate-900"
                  data-testid="scale-emoji-panel"
                >
                  <div class="grid grid-cols-8 gap-1">
                    <button
                      v-for="emoji in scaleEmojiList"
                      :key="emoji"
                      class="rounded-lg p-1 text-lg transition hover:bg-slate-100 dark:hover:bg-slate-800"
                      type="button"
                      @click="appendScaleEmoji(emoji)"
                    >
                      {{ emoji }}
                    </button>
                  </div>
                </div>
                <div class="grid grid-cols-5 gap-2">
                  <button
                    v-for="response in quickScaleResponses"
                    :key="response"
                    :data-testid="response === '经常' ? 'assessment-answer-strong' : undefined"
                    class="rounded-full bg-slate-100 px-2 py-2 text-xs font-semibold text-slate-600 transition hover:bg-primary hover:text-white dark:bg-slate-800 dark:text-slate-300"
                    :disabled="scaleInteractionLocked"
                    @click="sendScaleResponse(response)"
                  >
                    {{ response }}
                  </button>
                </div>
                <div class="flex gap-2">
                  <button
                    class="flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] border border-slate-200 bg-white text-slate-600 transition hover:border-primary hover:text-primary disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                    :class="scaleVoiceListening ? 'border-rose-200 bg-rose-50 text-rose-500 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300' : ''"
                    :disabled="scaleInteractionLocked || scaleVoiceBusy"
                    data-testid="scale-voice-input"
                    type="button"
                    @click="startScaleVoiceInput"
                  >
                    <StopCircle v-if="scaleVoiceListening" class="h-4 w-4" />
                    <Mic v-else class="h-4 w-4" />
                  </button>
                  <button
                    class="flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] border border-slate-200 bg-white text-slate-600 transition hover:border-primary hover:text-primary disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                    :class="scaleEmojiPickerOpen ? 'border-primary bg-primary/10 text-primary' : ''"
                    :disabled="scaleInteractionLocked || scaleVoiceBusy"
                    aria-label="选择表情"
                    :aria-pressed="scaleEmojiPickerOpen"
                    data-testid="scale-emoji-trigger"
                    type="button"
                    @click="scaleEmojiPickerOpen = !scaleEmojiPickerOpen"
                  >
                    <Smile class="h-4 w-4" />
                  </button>
                  <input
                    v-model="scaleInputText"
                    class="min-w-0 flex-1 rounded-[12px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900"
                    :placeholder="scaleInteractionLocked ? 'AI 正在回复中…' : scaleVoiceBusy ? '正在识别语音...' : scaleVoiceListening ? '正在聆听，请说出你的回答...' : '输入你的回答...'"
                    :readonly="scaleInteractionLocked"
                    data-testid="scale-dialogue-input"
                    @keyup.enter="sendScaleResponse()"
                  />
                  <button
                    class="flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] bg-primary text-white disabled:opacity-50"
                    :disabled="scaleInteractionLocked || !scaleInputText.trim()"
                    data-testid="scale-dialogue-send"
                    @click="sendScaleResponse()"
                  >
                    <Send class="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div v-else class="space-y-3 border-t border-slate-100 bg-white p-4 dark:border-slate-800 dark:bg-slate-950" data-testid="scale-report">
                <div class="rounded-[12px] bg-slate-50 p-4 dark:bg-slate-900">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-semibold text-slate-600 dark:text-slate-300">对话评估报告</span>
                    <span class="rounded-full px-3 py-1 text-xs font-bold" :class="scaleResult?.riskLevel === 'high' ? 'bg-rose-100 text-rose-700' : scaleResult?.riskLevel === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                      {{ scaleSummary.label }}
                    </span>
                  </div>
                  <p class="mt-2 text-4xl font-black text-slate-900 dark:text-white">{{ scaleResult?.score ?? 0 }} <span class="text-base text-slate-400">/ 27</span></p>
                  <p class="mt-2 text-sm leading-6 text-slate-500">{{ scaleSummary.summary }}</p>
                </div>
                <button class="w-full rounded-[12px] bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900" data-testid="scale-inline-next" @click="openVoiceAssessmentFromScale">
                  语音识别
                </button>
                <button class="w-full rounded-[12px] border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200" type="button" @click="retakeScaleAssessment">
                  重新测试量表
                </button>
              </div>
            </div>
            <button class="w-full rounded-[12px] border border-rose-200 bg-white px-4 py-3 text-sm font-semibold text-rose-500 dark:border-rose-800 dark:bg-slate-900" @click="openHtp">
              房树人(HTP)评估
            </button>
          </div>
        </BaseCard>

        <BaseCard v-show="!isMobile || step === 'voice'" class="flex h-full flex-col overflow-hidden" :class="isMobile ? 'rounded-none border-0 shadow-none' : ''" :padded="false">
          <div class="flex items-center gap-2 border-b border-slate-100 bg-gradient-to-r from-indigo-50 to-blue-50 px-5 py-3 dark:border-slate-800 dark:from-indigo-950/30 dark:to-blue-950/30">
            <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600 text-white">
              <Mic class="h-4 w-4" />
            </div>
            <span class="text-sm font-bold text-slate-800 dark:text-slate-100">语音情绪识别</span>
            <span :class="['ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ring-1', moduleStatusBadgeClass(voiceCompleted)]">
              {{ moduleStatusBadgeText(voiceCompleted) }}
            </span>
          </div>

          <div class="space-y-4 p-5">
            <div class="text-center">
              <div class="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                <Mic class="h-7 w-7" :class="voiceCaptureState === 'recording' ? 'animate-pulse text-rose-500' : 'text-primary'" />
              </div>
              <h2 class="text-xl font-black text-slate-900 dark:text-white">语音情绪识别</h2>
              <p class="text-xs text-slate-500">请朗读一段文字或随意诉说 10 秒，系统将分析您的语速、音调及能量分布。</p>
            </div>

            <div class="overflow-hidden rounded-[16px] border border-slate-100 bg-white p-4 shadow-lg dark:border-slate-800 dark:bg-slate-900" data-testid="voice-status-panel">
              <div class="flex h-28 items-center justify-center gap-[2px] px-2">
                <div
                  v-for="(height, index) in voiceWaveform"
                  :key="index"
                  class="w-[3px] rounded-full transition-all duration-150"
                  :style="{ height: `${voiceCaptureState === 'idle' ? 5 : height}%`, background: voiceCaptureState === 'recording' ? 'linear-gradient(to top, #7A3EF4, #EC4899)' : '#E2E8F0', opacity: voiceCaptureState === 'recording' ? 0.95 : 0.6 }"
                />
              </div>
              <div class="mt-4 flex items-center justify-center gap-3">
                <div class="flex items-center gap-2 rounded-full bg-slate-50 px-4 py-2 dark:bg-slate-950">
                  <span class="h-2 w-2 rounded-full" :class="voiceCaptureState === 'recording' ? 'animate-pulse bg-rose-500' : 'bg-slate-300'" />
                  <span class="text-xs font-medium text-slate-600 dark:text-slate-300">{{ voiceStatusLabel }}</span>
                </div>
                <div class="flex items-center gap-2 rounded-full bg-slate-50 px-4 py-2 dark:bg-slate-950">
                  <span class="text-xs text-slate-400">时长</span>
                  <span class="text-sm font-bold text-slate-700 dark:text-slate-200">{{ voiceDuration }}s</span>
                  <span class="text-xs text-slate-400">/ {{ voiceMaxDuration }}s</span>
                </div>
              </div>
              <div class="mt-4 space-y-2" data-testid="voice-recording-progress">
                <div class="flex justify-between text-xs text-slate-500">
                  <span>录音进度</span>
                  <span>{{ voiceRecordingProgress }}%</span>
                </div>
                <ProgressBar :value="voiceRecordingProgress" tone="from-violet-500 to-pink-500" />
              </div>
              <div v-if="voiceCaptureState === 'analyzing'" class="mt-4 space-y-2" data-testid="voice-analysis-progress">
                <div class="flex justify-between text-xs text-slate-500">
                  <span>分析进度</span>
                  <span class="font-bold text-[#7A3EF4]">{{ Math.round(voiceAnalysisProgress) }}%</span>
                </div>
                <ProgressBar :value="voiceAnalysisProgress" tone="from-violet-500 to-pink-500" />
              </div>
            </div>

            <div class="flex flex-col gap-3">
              <button
                class="h-12 w-full rounded-[12px] bg-[#1976ff] px-4 py-3 text-base font-black text-white shadow-lg shadow-blue-200 disabled:opacity-60"
                data-testid="assessment-voice-record"
                :disabled="voiceCaptureState === 'analyzing'"
                @click="voiceCaptureState === 'recording' ? stopVoiceCapture() : startVoiceCapture()"
              >
                <span class="inline-flex items-center gap-2">
                  <StopCircle v-if="voiceCaptureState === 'recording'" class="h-4 w-4" />
                  <Mic v-else class="h-4 w-4" />
                  {{ voiceCaptureState === 'recording' ? '停止采集' : '开始实时录音' }}
                </span>
              </button>
              <p v-if="voiceCompleted" class="text-center text-[11px] font-medium text-slate-400">
                可以重新录音，最终报告只保留最新一次语音结果。
              </p>
              <button
                class="h-12 w-full rounded-[12px] border border-slate-200 bg-white px-4 py-3 text-center text-sm font-black text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                :disabled="voiceCaptureState === 'recording' || voiceCaptureState === 'analyzing'"
                @click="audioInput?.click()"
              >
                <span class="inline-flex items-center gap-2">
                  <Upload class="h-4 w-4" />
                  上传音频文件
                </span>
              </button>
              <input ref="audioInput" class="hidden" data-testid="assessment-voice-upload" type="file" accept="audio/*" @change="handleVoiceUpload" />
            </div>

            <div
              v-if="voiceRecognizedText"
              class="rounded-[16px] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
              data-testid="voice-recognized-text"
            >
              <p class="mb-2 text-xs font-bold text-slate-400">语音识别内容</p>
              {{ voiceRecognizedText }}
            </div>

            <div class="flex gap-2 rounded-[12px] bg-primary/5 p-3 text-xs leading-5 text-primary/70">
              <Info class="mt-0.5 h-4 w-4 shrink-0" />
              <p>提示：请尽量在安静的环境下录音。当有效语音时长满 10s 且停顿在合理范围内时，系统将自动结束采集。</p>
            </div>
          </div>
        </BaseCard>

        <BaseCard v-show="!isMobile || step === 'expression'" class="flex h-full flex-col overflow-hidden bg-slate-950 text-white" :class="isMobile ? 'rounded-none border-0 shadow-none' : ''" :padded="false">
          <div class="flex items-center gap-2 border-b border-white/10 bg-gradient-to-b from-slate-900 to-slate-950 px-5 py-3">
            <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-600 text-white">
              <Video class="h-4 w-4" />
            </div>
            <span class="text-sm font-bold">表情识别</span>
            <span :class="['ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ring-1', moduleStatusBadgeClass(expressionCompleted, true)]">
              {{ moduleStatusBadgeText(expressionCompleted) }}
            </span>
          </div>

          <div class="space-y-4 p-5">
            <div v-if="!expressionCameraStarted" class="relative overflow-hidden rounded-[18px] border border-white/10 bg-gradient-to-br from-blue-950 via-slate-950 to-cyan-950 p-5 text-center" data-testid="expression-start-panel">
              <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-2xl shadow-blue-500/40">
                <ScanFace class="h-10 w-10 text-white" />
              </div>
              <h2 class="mt-5 text-2xl font-black">AI 表情识别分析</h2>
              <p class="mt-2 text-sm leading-6 text-white/70">通过面部微表情识别技术，分析情绪状态与心理健康指标。</p>
              <div class="mt-5 grid grid-cols-3 gap-3 text-center">
                <div class="rounded-2xl border border-white/15 bg-white/10 p-3">
                  <Shield class="mx-auto h-6 w-6 text-cyan-300" />
                  <p class="mt-2 text-xs font-bold">隐私保护</p>
                  <p class="mt-1 text-[10px] leading-tight text-white/55">本地处理，数据安全</p>
                </div>
                <div class="rounded-2xl border border-white/15 bg-white/10 p-3">
                  <Activity class="mx-auto h-6 w-6 text-cyan-300" />
                  <p class="mt-2 text-xs font-bold">实时分析</p>
                  <p class="mt-1 text-[10px] leading-tight text-white/55">9维情绪雷达图</p>
                </div>
                <div class="rounded-2xl border border-white/15 bg-white/10 p-3">
                  <ScanFace class="mx-auto h-6 w-6 text-cyan-300" />
                  <p class="mt-2 text-xs font-bold">微表情识别</p>
                  <p class="mt-1 text-[10px] leading-tight text-white/55">捕捉细微情绪变化</p>
                </div>
              </div>
            </div>

            <div v-else class="rounded-[18px] border border-white/10 bg-white/5 p-4" data-testid="expression-live-panel">
              <div class="relative flex h-72 items-center justify-center overflow-hidden rounded-[16px] border border-white/10 bg-slate-900">
                <video
                  v-show="expressionStream && expressionStatus !== 'completed'"
                  ref="expressionVideo"
                  autoplay
                  muted
                  playsinline
                  class="absolute inset-0 h-full w-full object-cover opacity-80"
                />
                <div class="absolute inset-0 bg-gradient-to-b from-slate-950/35 via-transparent to-slate-950/50" />
                <div class="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(59,130,246,0.10)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.10)_1px,transparent_1px)] [background-size:28px_28px]" />
                <div class="absolute left-4 top-4 z-20 space-y-1 text-left">
                  <span class="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/15 px-3 py-1 text-[10px] font-bold text-emerald-300">
                    <span class="h-1.5 w-1.5 rounded-full bg-emerald-300" />
                    LIVE FEED
                  </span>
                  <p class="font-mono text-[10px] leading-4 text-white/60">
                    FPS: <span :class="expressionFps < 15 ? 'text-rose-300' : 'text-emerald-300'">{{ expressionFps }}</span> · MODEL: Qwen3.5-397B-A17B · WIN: 10s<br />
                    FACE: <span :class="expressionNoFaceCount > 0 ? 'text-rose-300' : 'text-emerald-300'">{{ expressionNoFaceCount > 0 ? 'LOST' : 'LOCKED' }}</span>
                  </p>
                </div>
                <div class="absolute right-4 top-4 z-20 text-right">
                  <p class="font-mono text-4xl font-black">{{ String(expressionCountdown).padStart(2, '0') }}<span class="ml-1 text-sm text-white/40">S</span></p>
                  <div class="mt-1 h-1 w-32 overflow-hidden rounded-full bg-white/10">
                    <div class="h-full rounded-full bg-primary transition-all" :style="{ width: `${(expressionCountdown / 5) * 100}%` }" />
                  </div>
                </div>
                <div class="absolute left-1/2 top-1/2 z-10 aspect-[3/4] w-[58%] max-w-[240px] -translate-x-1/2 -translate-y-[53%] rounded-[32px] border border-primary/25">
                  <div class="absolute left-3 top-3 h-10 w-10 border-l-2 border-t-2 border-primary/60" />
                  <div class="absolute right-3 top-3 h-10 w-10 border-r-2 border-t-2 border-primary/60" />
                  <div class="absolute bottom-3 left-3 h-10 w-10 border-b-2 border-l-2 border-primary/60" />
                  <div class="absolute bottom-3 right-3 h-10 w-10 border-b-2 border-r-2 border-primary/60" />
                  <div v-if="expressionStatus === 'capturing'" class="absolute left-4 right-4 top-1/2 h-[2px] animate-pulse rounded-full bg-gradient-to-r from-transparent via-cyan-300 to-transparent shadow-[0_0_16px_rgba(59,130,246,0.8)]" />
                </div>
                <img
                  v-if="expressionSnapshot && expressionStatus === 'completed'"
                  :src="expressionSnapshot"
                  alt="Expression snapshot"
                  class="absolute inset-0 h-full w-full object-cover opacity-80"
                />
                <div v-if="expressionStatus === 'idle' || expressionStatus === 'completed' || expressionStatus === 'analyzing'" class="relative z-10 rounded-2xl bg-slate-950/55 px-5 py-4 text-center backdrop-blur">
                  <ScanFace class="mx-auto h-12 w-12 text-cyan-300" />
                  <p class="mt-3 text-sm font-bold">{{ expressionStatusText }}</p>
                  <p class="mt-1 text-xs text-white/60">将采集面部快照并调用多模态视觉分析。</p>
                </div>
              </div>
              <ProgressBar class="mt-4" :value="expressionStatus === 'capturing' ? (5 - expressionCountdown) * 20 : expressionProgress" tone="from-blue-500 to-cyan-400" />
              <div class="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                <div class="rounded-[12px] bg-white/5 p-3">
                  <p class="text-white/40">眉心</p>
                  <p class="mt-1 font-bold">{{ Math.round(expressionSignals.brow * 100) }}%</p>
                </div>
                <div class="rounded-[12px] bg-white/5 p-3">
                  <p class="text-white/40">嘴角</p>
                  <p class="mt-1 font-bold">{{ Math.round(expressionSignals.mouth * 100) }}%</p>
                </div>
                <div class="rounded-[12px] bg-white/5 p-3">
                  <p class="text-white/40">眨眼</p>
                  <p class="mt-1 font-bold">{{ Math.round(expressionSignals.blink * 100) }}%</p>
                </div>
              </div>
              <div class="mt-3 rounded-2xl border border-white/10 bg-slate-950/55 px-4 py-3">
                <div class="mb-2 flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="rounded-full border border-primary/30 bg-primary/20 px-2 py-0.5 text-[10px] font-bold text-primary">MICRO</span>
                    <span class="text-xs text-white/60">微表情信号</span>
                  </div>
                  <span class="font-mono text-[9px] text-white/40">{{ expressionStatus === 'capturing' ? 'ANALYZING' : 'READY' }}</span>
                </div>
                <div v-if="expressionNoFaceCount > 0" class="text-center text-[10px] font-bold text-rose-200/80">未检测到人脸，请将面部对准取景框</div>
              </div>
            </div>

            <div class="grid grid-cols-[48px_1fr_48px] items-center gap-4">
              <button class="grid h-12 w-12 place-items-center rounded-full text-white/70 hover:bg-white/10 hover:text-white" data-testid="expression-switch-camera" @click="switchExpressionCamera">
                <RefreshCcw class="h-5 w-5" />
              </button>
              <button
                class="flex h-[56px] items-center justify-center gap-3 rounded-full bg-cyan-500 px-6 text-sm font-black text-white shadow-lg shadow-cyan-900/30"
                data-testid="complete-expression"
                @click="completeExpression"
              >
                <Video class="h-4 w-4" />
                {{ !expressionCameraStarted ? '开始表情识别' : expressionStatus === 'idle' ? '开始采集' : expressionStatus === 'capturing' ? '立即分析' : expressionStatus === 'analyzing' ? 'AI分析中...' : '确认并生成多模态评估报告' }}
              </button>
              <button class="grid h-12 w-12 place-items-center rounded-full text-white/70 hover:bg-white/10 hover:text-white" type="button">
                <Maximize class="h-5 w-5" />
              </button>
            </div>
            <button
              v-if="expressionCompleted"
              class="w-full rounded-full border border-white/15 px-4 py-3 text-sm font-black text-white/80 transition hover:bg-white/10 hover:text-white"
              type="button"
              @click="retakeExpressionAssessment"
            >
              重新测试表情
            </button>
          </div>
        </BaseCard>
      </div>
    </div>

    <div v-if="voiceReportOpen && voiceReport" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="voice-report-dialog">
      <section class="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-[20px] bg-white shadow-xl dark:bg-slate-950">
        <header class="flex items-center justify-between bg-gradient-to-r from-[#7A3EF4] to-[#9F7AEA] px-4 py-3 text-white">
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
              <Activity class="h-5 w-5" />
            </div>
            <div>
              <h2 class="font-bold">语音识别完成</h2>
              <p class="text-xs text-white/80">声学特征分析与情绪模型匹配</p>
            </div>
          </div>
          <button @click="voiceReportOpen = false"><X class="h-5 w-5" /></button>
        </header>
        <div ref="voiceReportEl" class="space-y-4 overflow-y-auto p-4" id="voice-report-card">
          <div class="rounded-[12px] border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
            <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200">
              <FileText class="h-4 w-4 text-[#7A3EF4]" />
              语音识别内容
            </h3>
            <p class="mt-2 rounded-[8px] bg-white p-3 text-sm leading-6 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ voiceReport.text }}</p>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <div class="rounded-[12px] border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                <BarChart3 class="h-4 w-4 text-[#7A3EF4]" />
                核心声学指标
              </h3>
              <div class="mt-3 grid grid-cols-2 gap-2">
                <div class="rounded-[8px] bg-white p-3 dark:bg-slate-800">
                  <p class="text-[10px] font-bold uppercase text-slate-400">语速 (字/分)</p>
                  <div class="mt-1 flex items-end gap-1">
                    <span class="text-lg font-black text-slate-800 dark:text-white">{{ voiceReport.speechMetrics.speed }}</span>
                    <span class="mb-0.5 text-[10px] text-slate-400">参考: 120-180</span>
                  </div>
                  <span v-if="voiceReport.indicators.isLowSpeed" class="mt-1 inline-flex h-5 items-center rounded-full bg-rose-100 px-2 text-[10px] font-bold text-rose-700">过慢</span>
                </div>
                <div class="rounded-[8px] bg-white p-3 dark:bg-slate-800">
                  <p class="text-[10px] font-bold uppercase text-slate-400">语调基频 (Hz)</p>
                  <div class="mt-1 flex items-end gap-1">
                    <span class="text-lg font-black text-slate-800 dark:text-white">{{ voiceReport.speechMetrics.tone }}</span>
                    <span class="mb-0.5 text-[10px] text-slate-400">参考: 100-250</span>
                  </div>
                  <span v-if="voiceReport.indicators.isHighPitchDrop" class="mt-1 inline-flex h-5 items-center rounded-full bg-amber-100 px-2 text-[10px] font-bold text-amber-700">基频下降</span>
                </div>
                <div class="rounded-[8px] bg-white p-3 dark:bg-slate-800">
                  <p class="text-[10px] font-bold uppercase text-slate-400">停顿时长 (秒)</p>
                  <div class="mt-1 flex items-end gap-1">
                    <span class="text-lg font-black text-slate-800 dark:text-white">{{ voiceReport.speechMetrics.pause }}</span>
                    <span class="mb-0.5 text-[10px] text-slate-400">参考: &lt;1.5s</span>
                  </div>
                  <span v-if="voiceReport.indicators.isLongPause" class="mt-1 inline-flex h-5 items-center rounded-full bg-rose-100 px-2 text-[10px] font-bold text-rose-700">停顿过长</span>
                </div>
                <div class="rounded-[8px] bg-white p-3 dark:bg-slate-800">
                  <p class="text-[10px] font-bold uppercase text-slate-400">能量值 (dB)</p>
                  <div class="mt-1 flex items-end gap-1">
                    <span class="text-lg font-black text-slate-800 dark:text-white">{{ voiceReport.speechMetrics.energy }}</span>
                    <span class="mb-0.5 text-[10px] text-slate-400">参考: 60-80</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="rounded-[12px] border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                <Activity class="h-4 w-4 text-[#7A3EF4]" />
                8维情绪雷达
              </h3>
              <div class="relative mt-2 h-48 rounded-xl bg-white dark:bg-slate-950" data-testid="voice-radar-chart">
                <svg class="h-full w-full overflow-visible" viewBox="0 0 200 200" role="img" aria-label="8维情绪雷达图">
                  <defs>
                    <linearGradient id="voiceRadarGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#7A3EF4" stop-opacity="0.62" />
                      <stop offset="100%" stop-color="#EC4899" stop-opacity="0.32" />
                    </linearGradient>
                  </defs>
                  <polygon v-for="(grid, index) in voiceRadarGrid" :key="`voice-grid-${index}`" :points="grid" fill="none" stroke="#e2e8f0" stroke-width="1" />
                  <line v-for="point in voiceRadarItems" :key="`voice-axis-${point.key}`" x1="100" y1="100" :x2="point.labelX - (point.labelX - 100) * 0.25" :y2="point.labelY - (point.labelY - 100) * 0.25" stroke="#e2e8f0" stroke-width="1" />
                  <polygon :points="voiceRadarPolygon" fill="url(#voiceRadarGradient)" stroke="#7A3EF4" stroke-width="3" />
                  <circle v-for="point in voiceRadarItems" :key="`voice-point-${point.key}`" :cx="point.x" :cy="point.y" r="2.8" fill="#7A3EF4" />
                  <text
                    v-for="point in voiceRadarItems"
                    :key="`voice-label-${point.key}`"
                    :x="point.labelX"
                    :y="point.labelY"
                    text-anchor="middle"
                    dominant-baseline="middle"
                    class="fill-slate-500 text-[10px] font-semibold dark:fill-slate-300"
                  >
                    {{ point.label }}
                  </text>
                </svg>
                <div class="pointer-events-none absolute inset-1 rounded-xl border-2 border-[#7A3EF4]/20" />
              </div>
            </div>
          </div>
          <div class="flex gap-2 rounded-[12px] border border-indigo-100 bg-indigo-50 p-3 text-sm leading-6 text-indigo-800 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-200">
            <Info class="mt-1 h-4 w-4 shrink-0" />
            <div class="space-y-1">
              <p class="text-xs font-bold text-indigo-900 dark:text-indigo-100">智能分析建议</p>
              <p>{{ voiceReport.depressionAnalysis }}</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
            <div class="flex gap-2">
              <button
                class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200"
                data-testid="voice-report-export-pdf"
                @click="exportVoiceReport('pdf')"
              >
                <FileText class="h-3.5 w-3.5" />
                下载PDF
              </button>
              <button
                class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200"
                data-testid="voice-report-export-png"
                @click="exportVoiceReport('png')"
              >
                <Printer class="h-3.5 w-3.5" />
                导出PNG
              </button>
            </div>
            <button class="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#7A3EF4] px-4 text-xs font-bold text-white shadow-lg shadow-indigo-500/20" data-testid="voice-report-next" @click="completeVoice">
              表情识别
              <ChevronLeft class="h-3.5 w-3.5 rotate-180" />
            </button>
          </div>
        </div>
      </section>
    </div>

    <div v-if="scaleReportOpen && scaleResult" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="scale-completion-dialog">
      <section class="w-full max-w-md overflow-hidden rounded-[32px] bg-white shadow-2xl dark:bg-slate-950">
        <div class="space-y-4 bg-gradient-to-br from-primary to-fuchsia-500 p-8 text-center text-white">
          <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-white/20 backdrop-blur-md">
            <ClipboardList class="h-10 w-10" />
          </div>
          <div class="space-y-1">
            <h2 class="text-2xl font-black">评估完成</h2>
            <p class="text-sm text-white/70">基于您的多轮对话回答生成的报告</p>
          </div>
        </div>

        <div ref="scaleReportEl" class="space-y-8 bg-white p-8 dark:bg-slate-950" id="assessment-report-card">
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1 rounded-2xl bg-slate-50 p-4 text-center dark:bg-slate-900">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Score</span>
              <p class="text-3xl font-black text-primary">{{ scaleResult.score }}</p>
            </div>
            <div class="space-y-1 rounded-2xl bg-slate-50 p-4 text-center dark:bg-slate-900">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Risk</span>
              <p class="text-lg font-black" :class="scaleResult.riskLevel === 'high' ? 'text-rose-500' : scaleResult.riskLevel === 'medium' ? 'text-amber-500' : 'text-emerald-500'">
                {{ scaleSummary.label }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <h3 class="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100">
              <Info class="h-4 w-4 text-primary" />
              AI 建议
            </h3>
            <p class="text-sm leading-relaxed text-slate-500">{{ scaleAdviceText }}</p>
          </div>

          <div class="space-y-3 pt-4">
            <div class="flex gap-2">
              <button
                class="h-12 flex-1 rounded-xl border border-slate-100 text-sm font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
                data-testid="scale-report-export-pdf"
                type="button"
                @click="exportScaleReport('pdf')"
              >
                <Download class="mr-2 inline h-4 w-4" />
                PDF
              </button>
              <button
                class="h-12 flex-1 rounded-xl border border-slate-100 text-sm font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
                data-testid="scale-report-export-png"
                type="button"
                @click="exportScaleReport('png')"
              >
                <Printer class="mr-2 inline h-4 w-4" />
                PNG
              </button>
            </div>
            <button
              class="h-14 w-full rounded-2xl bg-primary text-lg font-bold text-white shadow-xl shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="scaleReadCountdown > 0"
              data-testid="scale-report-next"
              type="button"
              @click="openVoiceAssessmentFromScale"
            >
              {{ scaleReadCountdown > 0 ? `请阅读 (${scaleReadCountdown}s)` : '下一步：语音情绪识别' }}
            </button>
            <p class="px-4 text-center text-[10px] leading-relaxed text-slate-400">
              免责声明：本评估由 AI 生成，仅供参考。不代表临床诊断。如感不适请及时就医。
            </p>
          </div>
        </div>
      </section>
    </div>

    <div v-if="scaleHistoryOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="scale-history-dialog">
      <section class="flex max-h-[86vh] w-full max-w-2xl flex-col overflow-hidden rounded-[24px] bg-white shadow-xl dark:bg-slate-950">
        <header class="flex shrink-0 items-start justify-between border-b border-slate-100 px-6 py-5 dark:border-slate-800">
          <div>
            <h2 class="flex items-center gap-2 text-2xl font-black text-slate-900 dark:text-white">
              <History class="h-6 w-6 text-primary" />
              历史评估记录
            </h2>
            <p class="mt-1 text-sm text-slate-500">查看你的过往评估记录和分析报告</p>
          </div>
          <button class="grid h-9 w-9 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="scale-history-close" @click="scaleHistoryOpen = false">
            <X class="h-5 w-5 text-slate-400" />
          </button>
        </header>
        <div class="space-y-3 overflow-y-auto px-6 py-4">
          <button
            v-for="history in historyScaleAssessments"
            :key="history.id"
            class="group w-full rounded-2xl border border-slate-200 bg-white p-5 text-left transition hover:border-primary/30 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900"
            data-testid="scale-history-item"
            @click="openScaleHistoryDetail(history)"
          >
            <div class="flex items-start gap-4">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary group-hover:bg-primary/20">
                <ClipboardList class="h-6 w-6" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-3">
                  <h3 class="font-bold text-slate-800 transition group-hover:text-primary dark:text-slate-100">{{ history.scaleTypes.join(' + ') }}</h3>
                  <span class="shrink-0 rounded-full border px-2.5 py-1 text-xs font-bold" :class="scaleRiskInfo(history.riskLevel).badge">{{ scaleRiskInfo(history.riskLevel).label }}</span>
                </div>
                <div class="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                  <span class="inline-flex items-center gap-1"><Calendar class="h-3.5 w-3.5" />{{ formatScaleHistoryDate(history.date) }}</span>
                  <span class="inline-flex items-center gap-1"><AlertCircle class="h-3.5 w-3.5" />得分: {{ history.score }}</span>
                </div>
                <p class="mt-2 line-clamp-2 text-sm text-slate-600 dark:text-slate-400">{{ history.summary }}</p>
              </div>
              <ChevronLeft class="mt-3 h-5 w-5 rotate-180 text-slate-300 transition group-hover:translate-x-1 group-hover:text-primary" />
            </div>
          </button>
        </div>
      </section>
    </div>

    <div v-if="scaleHistoryDetailOpen && selectedScaleHistory" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="scale-history-detail-dialog">
      <section class="flex max-h-[88vh] w-full max-w-3xl flex-col overflow-hidden rounded-[24px] bg-white shadow-xl dark:bg-slate-950">
        <header class="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-5 dark:border-slate-800">
          <div>
            <h2 class="text-2xl font-black text-slate-900 dark:text-white">{{ selectedScaleHistory.scaleTypes.join(' + ') }} 评估记录</h2>
            <p class="mt-1 text-sm text-slate-500">{{ formatScaleHistoryDate(selectedScaleHistory.date) }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button class="inline-flex h-10 items-center gap-2 rounded-xl bg-primary px-4 text-sm font-bold text-white shadow-md" data-testid="scale-history-view-report" @click="scaleHistoryReportOpen = true">
              <FileText class="h-4 w-4" />
              查看报告
            </button>
            <button class="grid h-10 w-10 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" @click="closeScaleHistoryDetail(true)">
              <X class="h-5 w-5 text-slate-400" />
            </button>
          </div>
        </header>
        <div class="flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <div
            v-for="(message, index) in selectedScaleHistory.messages"
            :key="`${selectedScaleHistory.id}-${index}`"
            class="flex gap-2"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div v-if="message.role === 'assistant'" class="h-9 w-9 shrink-0 overflow-hidden rounded-full border-2 border-slate-100 bg-gradient-to-br from-blue-500 to-indigo-500 dark:border-slate-800">
              <img :src="doctorAvatarUrl" alt="管理员头像" class="h-full w-full object-cover" />
            </div>
            <div
              class="max-w-[72%] rounded-3xl px-4 py-3 text-sm font-medium leading-6 shadow-sm"
              :class="message.role === 'user' ? 'rounded-tr-none bg-primary text-white shadow-primary/10' : 'rounded-tl-none border border-slate-100 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200'"
            >
              {{ message.content }}
            </div>
            <div v-if="message.role === 'user'" class="h-9 w-9 shrink-0 overflow-hidden rounded-full border-2 border-primary/20">
              <img v-if="userAvatarSource.imageUrl" :src="userAvatarSource.imageUrl" alt="用户头像" class="h-full w-full object-cover" />
              <span v-else :class="['flex h-full w-full items-center justify-center text-sm font-bold', userAvatarSource.preset?.bg || 'bg-gradient-to-br from-primary to-primary/80 text-white']">
                {{ userAvatarSource.preset?.emoji || userInitial }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="scaleHistoryReportOpen && selectedScaleHistory" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4" data-testid="scale-history-report-dialog">
      <section class="max-h-[88vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-xl dark:bg-slate-950">
        <header class="bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 p-6 text-white">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
              <FileText class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-2xl font-bold">对话评估报告</h2>
              <p class="mt-1 text-sm text-white/80">PHQ-9 抑郁症筛查量表详细得分与分析</p>
              <p class="mt-1 text-xs text-white/60">{{ formatScaleHistoryDate(selectedScaleHistory.date) }}</p>
            </div>
          </div>
        </header>
        <div class="space-y-6 p-6">
          <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-5 shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
            <div class="flex items-center justify-between">
              <span class="font-medium text-slate-600 dark:text-slate-300">PHQ-9 总分</span>
              <span class="rounded-full px-3 py-1 text-xs font-bold text-white" :class="scaleRiskInfo(selectedScaleHistory.reportData.riskLevel).solid">{{ scaleRiskInfo(selectedScaleHistory.reportData.riskLevel).label }}</span>
            </div>
            <p class="mt-3 text-4xl font-black text-slate-900 dark:text-white">{{ selectedScaleHistory.reportData.score }} <span class="text-lg text-slate-400">/ 27</span></p>
            <p class="mt-3 text-sm leading-6 text-slate-500">根据您的量表回答，您的抑郁倾向处于{{ scaleRiskInfo(selectedScaleHistory.reportData.riskLevel).label }}水平。</p>
          </div>
          <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
            <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-blue-500" />各维度得分详情</h3>
            <div class="mt-4 grid grid-cols-3 gap-3">
              <div v-for="item in scaleHistoryDimensions(selectedScaleHistory)" :key="item.label" class="rounded-lg border border-slate-100 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
                <p class="text-xs text-slate-500">{{ item.label }}</p>
                <p class="mt-1 text-lg font-bold" :class="item.score >= 2 ? 'text-amber-500' : item.score >= 1 ? 'text-blue-500' : 'text-emerald-500'">{{ item.score }} <span class="text-xs text-slate-400">/ {{ item.max || 3 }}</span></p>
              </div>
            </div>
          </div>
          <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
            <h3 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200"><Info class="h-4 w-4 text-blue-500" />AI 专业建议</h3>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ selectedScaleHistory.reportData.suggestion }}</p>
          </div>
          <div class="flex justify-end gap-3">
            <button class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" data-testid="scale-history-report-export" @click="exportFusionReport('pdf')">
              <Download class="mr-2 inline h-4 w-4" />
              导出报告
            </button>
            <button class="rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" data-testid="scale-history-report-close" @click="scaleHistoryReportOpen = false">
              关闭
            </button>
          </div>
        </div>
      </section>
    </div>

    <div v-if="expressionReportOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="expression-report-dialog">
      <section class="max-h-[95vh] w-full max-w-3xl overflow-hidden rounded-[20px] bg-white shadow-xl dark:bg-slate-950">
        <header class="flex items-start justify-between bg-gradient-to-r from-[#7A3EF4] to-[#9F7AEA] p-4 text-white">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-full bg-white/20">
              <ScanFace class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-lg font-bold">表情识别完成</h2>
              <p class="text-xs text-white/80">微表情特征与抑郁风险关联分析</p>
            </div>
          </div>
          <button @click="expressionReportOpen = false"><X class="h-5 w-5" /></button>
        </header>

        <div id="expression-report-card" class="max-h-[72vh] overflow-y-auto p-4" data-testid="expression-report-card">
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-3">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                <ScanFace class="h-4 w-4 text-[#7A3EF4]" />
                微表情表征图
              </h3>
              <div class="space-y-3">
                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                  <p class="text-[10px] font-bold uppercase text-slate-400">眉心皱纹 (Brow Furrow)</p>
                  <p class="mt-1 text-sm font-medium leading-snug text-slate-700 dark:text-slate-200">{{ getExpressionMicroFeatureText('brow_furrow') }}</p>
                </div>
                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                  <p class="text-[10px] font-bold uppercase text-slate-400">嘴角形态 (Mouth Droop)</p>
                  <p class="mt-1 text-sm font-medium leading-snug text-slate-700 dark:text-slate-200">{{ getExpressionMicroFeatureText('mouth_droop') }}</p>
                </div>
                <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                  <p class="text-[10px] font-bold uppercase text-slate-400">眼神接触 (Eye Contact)</p>
                  <p class="mt-1 text-sm font-medium leading-snug text-slate-700 dark:text-slate-200">{{ getExpressionMicroFeatureText('eye_contact') }}</p>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
              <h3 class="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                <Activity class="h-4 w-4 text-[#7A3EF4]" />
                9维情绪雷达
              </h3>
              <div class="relative mx-auto mt-3 h-56 max-w-72 rounded-2xl bg-white dark:bg-slate-950" data-testid="expression-radar-chart">
                <svg class="h-full w-full overflow-visible" viewBox="0 0 200 200" role="img" aria-label="9维情绪雷达图">
                  <polygon v-for="(grid, index) in expressionRadarGrid" :key="`expression-grid-${index}`" :points="grid" fill="none" stroke="#e2e8f0" stroke-width="1" />
                  <line v-for="point in expressionRadarPoints" :key="`expression-axis-${point.key}`" x1="100" y1="100" :x2="point.labelX - (point.labelX - 100) * 0.25" :y2="point.labelY - (point.labelY - 100) * 0.25" stroke="#e2e8f0" stroke-width="1" />
                  <polygon :points="expressionRadarPolygon" fill="#7A3EF4" fill-opacity="0.38" stroke="#7A3EF4" stroke-width="2.5" />
                  <circle v-for="point in expressionRadarPoints" :key="`expression-point-${point.key}`" :cx="point.x" :cy="point.y" r="2.5" fill="#7A3EF4" />
                  <text
                    v-for="point in expressionRadarPoints"
                    :key="`expression-label-${point.key}`"
                    :x="point.labelX"
                    :y="point.labelY"
                    text-anchor="middle"
                    dominant-baseline="middle"
                    class="fill-slate-500 text-[9px] font-semibold dark:fill-slate-300"
                  >
                    {{ point.label }}
                  </text>
                </svg>
              </div>
            </div>
          </div>

          <div class="mt-4 flex gap-3 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-indigo-800 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-200">
            <Info class="mt-1 h-5 w-5 shrink-0" />
            <div>
              <p class="font-bold">AI 综合分析</p>
              <p class="mt-1">{{ expressionAiReport?.analysis_report || expressionSummary.summary }}</p>
            </div>
          </div>
        </div>

        <footer class="flex items-center justify-between gap-3 border-t border-slate-100 p-4 dark:border-slate-800">
          <div class="flex gap-2">
            <button class="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportFusionReport('pdf')">
              <FileText class="mr-1 inline h-3 w-3" />
              下载PDF
            </button>
            <button class="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportFusionReport('png')">
              <Download class="mr-1 inline h-3 w-3" />
              导出PNG
            </button>
          </div>
          <button class="rounded-lg bg-[#7A3EF4] px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-500/20" data-testid="expression-report-complete" @click="completeExpression">
            综合报告
            <ChevronLeft class="ml-1 inline h-3 w-3 rotate-180" />
          </button>
        </footer>
      </section>
    </div>
  </div>
</template>
