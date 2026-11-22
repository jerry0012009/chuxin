<script setup lang="ts">
import {
  Award,
  Bookmark,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  CloudRain,
  Copy,
  Eye,
  FileText,
  Flame,
  Gamepad2,
  Heart,
  Hand,
  ImagePlus,
  Link2,
  LoaderCircle,
  MessageCircle,
  Mic,
  Music,
  Pause,
  PenLine,
  Play,
  Plus,
  Repeat,
  Repeat1,
  Search,
  Save,
  Share2,
  Shuffle,
  SkipBack,
  SkipForward,
  Sparkles,
  Smartphone,
  Smile,
  Star,
  Target,
  TrendingUp,
  Trophy,
  StopCircle,
  Sun,
  ThumbsUp,
  Volume2,
  VolumeX,
  X,
  Zap,
  MoveUp,
  MoveDown,
  MoveLeft,
  MoveRight,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import { useAuthSession } from '@/composables/useAuthSession'
import { useAppState } from '@/composables/useAppState'
import { moodMeta } from '@/data/static'
import {
  nswMandarinMindfulnessArticleBodies,
  nswMandarinMindfulnessContents,
  nswMandarinMindfulnessTrackContentIds,
} from '@/data/nsw-mindfulness'
import {
  createMeditationSession,
  completeInterventionItem,
  getHealingContents,
  getMeditationStats,
  getUserFavorites,
  incrementLikeCount,
  incrementViewCount,
  speechRecognition,
  startInterventionItem,
  toggleFavorite,
  updateEmotionDiary,
} from '@/db/api'
import type { DiaryEntry, HealingContent, MoodLevel } from '@/types'
import { blobToBase64, convertWebmToWav } from '@/utils/audio'
import { publicAssetUrl } from '@/utils/public-assets'

type HealingTab = 'meditation' | 'game' | 'diary' | 'knowledge'
type MeditationCategory = 'all' | 'relax' | 'sleep' | 'focus'
type LoopMode = 'all' | 'one' | 'shuffle'

interface MeditationStats {
  totalMinutes: number
  totalSessions: number
}

const route = useRoute()
const router = useRouter()
const { state: authState } = useAuthSession()
const { createEmotionRecord, loadEmotionRecords, meditationTracks, state, sortedDiaries } = useAppState()

type HealingRouteState = {
  activeTab?: HealingTab
  activeCategory?: MeditationCategory
  trackIndex?: number
}

const readRouteState = (): HealingRouteState => {
  const raw = window.history.state || {}
  return {
    activeTab: raw.activeTab,
    activeCategory: raw.activeCategory,
    trackIndex: typeof raw.trackIndex === 'number' ? raw.trackIndex : undefined,
  }
}

const initialRouteState = readRouteState()
const initialTrackFromState = initialRouteState.trackIndex !== undefined
  ? meditationTracks[initialRouteState.trackIndex]?.id
  : undefined

const activeTab = ref<HealingTab>(initialRouteState.activeTab || ((route.query.tab as HealingTab) || 'meditation'))
const activeCategory = ref<MeditationCategory>(initialRouteState.activeCategory || ((route.query.category as MeditationCategory) || 'all'))
const selectedTrackId = ref(initialTrackFromState || (route.query.track as string) || meditationTracks[0]?.id || '')
const audioRef = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const totalTime = ref(0)
const buffering = ref(false)
const playError = ref('')
const loopMode = ref<LoopMode>('all')
const volume = ref(0.85)
const muted = ref(false)
const savingSession = ref(false)
const loadingStats = ref(false)
const meditationStats = ref<MeditationStats>({ totalMinutes: 0, totalSessions: 0 })
const moodDialogOpen = ref(false)
const moodAfter = ref('calmer')
const sessionNotes = ref('')
const toastMessage = ref('')
const toastTone = ref<'success' | 'error' | 'info'>('info')
const favoriteContentIds = ref<Set<string>>(new Set())
const favoriteSavingId = ref('')
const healingContents = ref<HealingContent[]>([])
const diaryMonthCursor = ref(new Date())
const diarySelectedDate = ref(new Date())
const diaryMood = ref<MoodLevel>('neutral')
const diaryContent = ref('')
const diaryTriggers = ref<string[]>([])
const diaryImages = ref<string[]>([])
const diaryPositiveExtra = ref<string[]>([])
const diaryNegativeExtra = ref<string[]>([])
const diaryNewPositiveTag = ref('')
const diaryNewNegativeTag = ref('')
const diarySaving = ref(false)
const diaryRecognizing = ref(false)
const diaryRecording = ref(false)
const diaryFeedbackType = ref<'giver' | 'receiver' | null>(null)
const diaryFileInput = ref<HTMLInputElement | null>(null)
const knowledgeSearchQuery = ref('')
const knowledgeSelectedType = ref<'all' | 'article' | 'video'>('all')
const knowledgeSortTab = ref<'all' | 'trending' | 'latest'>('all')
const selectedKnowledgeContent = ref<HealingContent | null>(null)
const knowledgeDetailOpen = ref(false)
const knowledgeShareDialogOpen = ref(false)
const knowledgeVideoError = ref('')
const generatedVideoThumbnails = ref<Record<string, string>>({})
const videoThumbnailLoading = ref<Record<string, boolean>>({})
const completedSession = ref<{
  contentId: string
  title: string
  duration: number
} | null>(null)
const interventionCompleted = ref(false)
const interventionCompleting = ref(false)
const interventionRemaining = ref(0)
let cleanupAudioListeners: (() => void) | null = null
let diaryMediaRecorder: MediaRecorder | null = null
let diaryAudioChunks: Blob[] = []
let diaryVoiceStream: MediaStream | null = null
let toastTimer: number | null = null
let interventionTimer: number | null = null

const tabs = [
  { key: 'meditation' as const, label: '冥想', icon: Music },
  { key: 'game' as const, label: '游戏', icon: Gamepad2 },
  { key: 'diary' as const, label: '日记', icon: PenLine },
  { key: 'knowledge' as const, label: '知识', icon: Bookmark },
]

const categoryMeta = [
  { key: 'all' as const, label: '全部', icon: Sparkles, tone: 'from-violet-400 to-purple-500' },
  { key: 'relax' as const, label: '放松', icon: Sparkles, tone: 'from-sky-400 to-blue-500' },
  { key: 'sleep' as const, label: '睡眠', icon: Music, tone: 'from-indigo-400 to-violet-500' },
  { key: 'focus' as const, label: '专注', icon: Zap, tone: 'from-amber-400 to-orange-500' },
]

const moodOptions = [
  { value: 'calmer', label: '更平静', emoji: '🌿' },
  { value: 'relaxed', label: '放松了', emoji: '☁️' },
  { value: 'focused', label: '更专注', emoji: '🎯' },
  { value: 'sleepy', label: '想休息', emoji: '🌙' },
  { value: 'unchanged', label: '变化不明显', emoji: '·' },
]

const positiveTriggers = ['好消息', '与朋友相聚', '顺利完成任务', '感恩时刻', '运动', '社交活动', '阳光/好天气', '音乐', '阅读', '兴趣爱好', '宠物陪伴', '冥想', '健康饮食']
const negativeTriggers = ['睡眠不足', '工作压力', '家庭琐事', '天气阴郁', '身体不适', '学习困难', '人际关系', '经济压力', '饮食不规律', '通勤拥堵', '争执/冲突', '其他']
const positiveTriggerSet = new Set(positiveTriggers)
const negativeTriggerSet = new Set(negativeTriggers)
const moodEntries = Object.entries(moodMeta) as Array<[MoodLevel, (typeof moodMeta)[MoodLevel]]>

const trackContentIds: Record<string, string> = {
  m1: 'dddd4444-4444-4444-4444-444444444444',
  m2: 'eeee5555-5555-5555-5555-555555555555',
  m3: 'ffff6666-6666-6666-6666-666666666666',
  m4: '9999aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  m5: '77778888-8888-8888-8888-888888888888',
  ...nswMandarinMindfulnessTrackContentIds,
}

const interventionRecordId = computed(() => String(route.query.interventionRecordId || ''))
const interventionReturnTo = computed(() => String(route.query.returnTo || '/assessment-tasks'))
const interventionTargetRefId = computed(() => String(route.query.targetRefId || ''))
const isInterventionMode = computed(() => Boolean(interventionRecordId.value))
const canCompleteIntervention = computed(() => !isInterventionMode.value || interventionRemaining.value <= 0 || interventionCompleted.value)

const gameUrl = 'https://poki.com/zh/g/temple-run-2-holi-festival#fullscreen'
const publicBaseUrl = import.meta.env.BASE_URL || '/'
const templeRunIconUrl = `${publicBaseUrl.replace(/\/?$/, '/')}temple_run_2_icon.png`
const gameControls = [
  { label: '上滑 - 跳跃', icon: MoveUp, tone: 'bg-orange-50 text-orange-500' },
  { label: '下滑 - 下蹲', icon: MoveDown, tone: 'bg-blue-50 text-blue-500' },
  { label: '左滑 - 左转', icon: MoveLeft, tone: 'bg-purple-50 text-purple-500' },
  { label: '右滑 - 右转', icon: MoveRight, tone: 'bg-emerald-50 text-emerald-500' },
]

const knowledgeTypes = [
  { key: 'all' as const, label: '全部', icon: Bookmark, tone: 'from-violet-500 to-fuchsia-500' },
  { key: 'article' as const, label: '文章', icon: FileText, tone: 'from-sky-500 to-cyan-500' },
  { key: 'video' as const, label: '视频', icon: Play, tone: 'from-rose-500 to-pink-500' },
]

const knowledgeSortTabs = [
  { key: 'all' as const, label: '推荐', icon: Sparkles, tone: 'from-violet-500 to-fuchsia-500' },
  { key: 'trending' as const, label: '热门', icon: TrendingUp, tone: 'from-orange-500 to-red-500' },
  { key: 'latest' as const, label: '最新', icon: Clock3, tone: 'from-green-500 to-teal-500' },
]

const localVideoByTitle: Record<string, string> = {
  正念冥想入门指南: '/srcs/video/正念冥想.mp4',
  正念冥想: '/srcs/video/正念冥想.mp4',
  睡眠与心理健康: '/srcs/video/睡眠与心理健康.mp4',
  睡眠与心理健康的关系: '/srcs/video/睡眠与心理健康.mp4',
  运动与心理健康: '/srcs/video/运动与心理健康.mp4',
  运动如何改善心理健康: '/srcs/video/运动与心理健康.mp4',
}

const articleBodyByTitle: Record<string, string> = {
  ...nswMandarinMindfulnessArticleBodies,
  '认识抑郁症:症状与诊断': `抑郁症是一种常见但可治疗的心理疾病。它并不是简单的“心情不好”，而是持续影响情绪、兴趣、精力、睡眠、食欲和自我评价的一组症状。

常见表现包括持续情绪低落、对原本喜欢的事情失去兴趣、容易疲惫、睡眠变差或睡眠过多、注意力下降、食欲和体重变化，以及明显的自责或无价值感。如果这些表现持续两周以上，并影响学习、工作或人际关系，就需要认真对待。

诊断通常需要结合标准化量表、临床访谈和生活功能评估。PHQ-9、HAMD 等量表可以帮助初步筛查，但不能替代专业诊断。

治疗方式包括心理治疗、药物治疗、运动和睡眠干预、社会支持等。大多数患者在规范治疗和持续支持下可以明显改善。`,
  如何应对焦虑情绪: `焦虑是人在面对压力和不确定性时的自然反应。适度焦虑可以帮助我们保持警觉，但当焦虑过强、持续太久，或影响睡眠、工作和生活时，就需要主动调节。

可以先从身体层面入手：进行缓慢腹式呼吸，吸气 4 秒、停顿 2 秒、呼气 6 秒，重复 3 到 5 分钟。也可以尝试渐进式肌肉放松，从脚趾到肩颈逐步收紧再放松肌肉。

认知层面可以记录让你焦虑的念头，区分“事实”和“推测”。把“我肯定做不好”改写为“我担心做不好，但可以先完成最小一步”，能降低灾难化思维带来的压力。

如果焦虑伴随明显惊恐发作、持续失眠或回避行为，建议寻求专业心理咨询或精神科评估。`,
  '认知行为疗法(CBT)介绍': `认知行为疗法（CBT）是一种结构化、目标明确的心理治疗方法。它的核心观点是：影响我们情绪的，往往不是事件本身，而是我们对事件的解释和看法。

CBT 通常会关注三个层次的认知：自动思维、中间信念和核心信念。自动思维是具体情境下快速出现的念头，例如“我又失败了”。中间信念包括规则和假设，例如“我必须表现完美”。核心信念则更深层，例如“我不够好”。

治疗过程中，咨询师会帮助来访者识别这些想法，检验证据，寻找更平衡的解释，并通过行为实验、行为激活、问题解决训练等方式改变旧有模式。

CBT 通常持续 8 到 20 次，适用于抑郁、焦虑、强迫、睡眠问题和压力管理等场景。`,
  家人如何支持抑郁症患者: `支持抑郁症患者，首先要理解这不是“想不开”或“不努力”，而是一种真实的身心疾病。患者可能出现低落、迟缓、疲惫、回避社交和自责，这些表现需要被看见，而不是被责备。

陪伴时尽量避免说“想开点”“你就是太脆弱了”。更有效的表达是：“我看到你很难受，我愿意陪你一起面对。”倾听时不急着给建议，先确认对方的感受。

在生活中，可以帮助患者维持基本作息，例如一起散步、准备简单饮食、提醒就医或按医嘱服药。目标不要过高，能完成一点点就是进展。

如果患者表达自伤、自杀想法，或出现明显危险行为，需要立即联系家属、管理员或当地紧急救助资源。`,
}

const normalizeHealingContent = (content: HealingContent): HealingContent => {
  const fallbackVideoUrl = content.content_type === 'video'
    ? Object.entries(localVideoByTitle).find(([title]) => content.title.includes(title))?.[1]
    : undefined
  return {
    ...content,
    content_url: publicAssetUrl(content.content_url || fallbackVideoUrl),
    thumbnail_url: publicAssetUrl(content.thumbnail_url),
  }
}

const mergeLocalHealingContents = (contents: HealingContent[]) => {
  const byId = new Map<string, HealingContent>()
  nswMandarinMindfulnessContents.forEach((content) => byId.set(content.id, normalizeHealingContent(content)))
  contents.forEach((content) => byId.set(content.id, normalizeHealingContent(content)))
  return Array.from(byId.values())
}

const knowledgeThumbnail = (content: HealingContent | null | undefined) => {
  if (!content) return ''
  return content.thumbnail_url || generatedVideoThumbnails.value[content.id] || ''
}

const generateVideoThumbnail = (content: HealingContent) => {
  if (content.content_type !== 'video' || content.thumbnail_url || !content.content_url) return
  if (generatedVideoThumbnails.value[content.id] || videoThumbnailLoading.value[content.id]) return
  if (typeof document === 'undefined') return

  videoThumbnailLoading.value = { ...videoThumbnailLoading.value, [content.id]: true }
  const video = document.createElement('video')
  video.crossOrigin = 'anonymous'
  video.muted = true
  video.playsInline = true
  video.preload = 'metadata'
  video.src = content.content_url

  let timeoutId = 0
  const cleanup = () => {
    window.clearTimeout(timeoutId)
    video.onloadeddata = null
    video.onseeked = null
    video.onerror = null
    video.removeAttribute('src')
    video.load()
    videoThumbnailLoading.value = { ...videoThumbnailLoading.value, [content.id]: false }
  }

  video.onloadeddata = () => {
    try {
      video.currentTime = Math.min(0.1, Math.max(0, (video.duration || 1) / 10))
    } catch {
      cleanup()
    }
  }
  video.onseeked = () => {
    try {
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 360
      const context = canvas.getContext('2d')
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height)
        generatedVideoThumbnails.value = {
          ...generatedVideoThumbnails.value,
          [content.id]: canvas.toDataURL('image/jpeg', 0.8),
        }
      }
    } finally {
      cleanup()
    }
  }
  video.onerror = cleanup
  timeoutId = window.setTimeout(cleanup, 5000)
  video.load()
}

const generateMissingVideoThumbnails = () => {
  healingContents.value.forEach(generateVideoThumbnail)
}

const openTempleRun = () => {
  window.open(gameUrl, '_blank')
}

const clearInterventionTimer = () => {
  if (interventionTimer !== null) {
    window.clearInterval(interventionTimer)
    interventionTimer = null
  }
}

const startInterventionCountdown = () => {
  clearInterventionTimer()
  if (!isInterventionMode.value) return
  interventionCompleted.value = false
  interventionRemaining.value = Math.max(1, Number(route.query.duration || 10))
  interventionTimer = window.setInterval(() => {
    interventionRemaining.value -= 1
    if (interventionRemaining.value <= 0) clearInterventionTimer()
  }, 1000)
  void startInterventionItem(interventionRecordId.value).catch(() => {})
}

const completeCurrentIntervention = async (payload: Record<string, unknown>) => {
  if (!interventionRecordId.value || interventionCompleted.value) return
  if (!canCompleteIntervention.value) {
    showToast(`请等待 ${interventionRemaining.value} 秒后再完成`, 'info')
    return
  }
  interventionCompleting.value = true
  try {
    await completeInterventionItem(interventionRecordId.value, payload)
    interventionCompleted.value = true
    showToast('干预任务已同步完成', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '干预任务同步失败', 'error')
  } finally {
    interventionCompleting.value = false
  }
}

const completeGameIntervention = () => completeCurrentIntervention({
  source_ref_table: 'external_game',
  source_ref_id: 'temple-run-2',
  duration_seconds: Math.max(10, Number(route.query.duration || 10)),
  summary_json: { title: 'Temple Run 2 跑酷体验' },
})

const completeKnowledgeIntervention = () => {
  const content = selectedKnowledgeContent.value
  if (!content) return
  return completeCurrentIntervention({
    source_ref_table: 'healing_contents',
    source_ref_id: content.id,
    duration_seconds: Math.max(10, Number(route.query.duration || 10)),
    summary_json: { title: content.title, contentType: content.content_type },
  })
}

onMounted(() => {
  if (initialRouteState.activeTab || initialRouteState.activeCategory || initialRouteState.trackIndex !== undefined) {
    router.replace({ path: route.path, query: route.query, state: {} })
  }
})

const filteredTracks = computed(() =>
  activeCategory.value === 'all'
    ? meditationTracks
    : meditationTracks.filter((item) => item.category === activeCategory.value),
)

const selectedTrack = computed(() => {
  return meditationTracks.find((item) => item.id === selectedTrackId.value) ?? filteredTracks.value[0] ?? meditationTracks[0]!
})

const dateKey = (date: Date) => date.toISOString().slice(0, 10)

const diaryMonthLabel = computed(() =>
  diaryMonthCursor.value.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' }),
)

const diarySelectedDateKey = computed(() => dateKey(diarySelectedDate.value))

const diarySelectedDateLabel = computed(() =>
  diarySelectedDate.value.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }),
)

const diaryCalendarDays = computed(() => {
  const year = diaryMonthCursor.value.getFullYear()
  const month = diaryMonthCursor.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const days: Array<Date | null> = []
  for (let index = 0; index < firstDay.getDay(); index += 1) days.push(null)
  for (let day = 1; day <= lastDay.getDate(); day += 1) days.push(new Date(year, month, day))
  return days
})

const diariesByDate = computed(() => {
  const map = new Map<string, DiaryEntry[]>()
  sortedDiaries.value.forEach((item) => {
    const list = map.get(item.date) || []
    list.push(item)
    map.set(item.date, list)
  })
  return map
})

const selectedDateDiary = computed(() => diariesByDate.value.get(diarySelectedDateKey.value)?.[0] || null)

const diaryInsights = computed(() => {
  const weekAgo = new Date()
  weekAgo.setDate(weekAgo.getDate() - 7)
  const weekly = sortedDiaries.value.filter((item) => new Date(item.date).getTime() >= new Date(weekAgo.toDateString()).getTime())
  const positiveCount = sortedDiaries.value.filter((item) => item.mood === 'very_good' || item.mood === 'good').length
  return {
    latestCount: sortedDiaries.value.length,
    weeklyCount: weekly.length,
    positivePercent: Math.round((positiveCount / Math.max(1, sortedDiaries.value.length)) * 100),
  }
})

const diaryMoodTrend = computed(() => {
  const maxCount = Math.max(
    ...moodEntries.map(([key]) => sortedDiaries.value.filter((item) => item.mood === key).length),
    1,
  )
  return moodEntries.map(([key, meta]) => {
    const count = sortedDiaries.value.filter((item) => item.mood === key).length
    return {
      key,
      ...meta,
      count,
      width: `${Math.round((count / maxCount) * 100)}%`,
    }
  })
})

const commonDiaryTags = computed(() => {
  const countMap = new Map<string, number>()
  sortedDiaries.value.forEach((item) => {
    item.triggers.forEach((tag) => countMap.set(tag, (countMap.get(tag) || 0) + 1))
  })
  return Array.from(countMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([tag, count]) => ({ tag, count, positive: positiveTriggerSet.has(tag) }))
})

const selectedDiaryPositiveTriggers = computed(() =>
  diaryTriggers.value.filter((item) => positiveTriggerSet.has(item) || diaryPositiveExtra.value.includes(item)),
)

const selectedDiaryNegativeTriggers = computed(() =>
  diaryTriggers.value.filter((item) => negativeTriggerSet.has(item) || diaryNegativeExtra.value.includes(item)),
)

const knowledgeContents = computed(() =>
  healingContents.value.filter((item) => item.content_type === 'article' || item.content_type === 'video'),
)

const filteredKnowledgeContents = computed(() => {
  const query = knowledgeSearchQuery.value.trim().toLowerCase()
  let items = knowledgeContents.value.filter((item) => {
    if (knowledgeSelectedType.value !== 'all' && item.content_type !== knowledgeSelectedType.value) return false
    if (!query) return true
    return [item.title, item.description, item.author]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  })
  if (knowledgeSortTab.value === 'trending') {
    items = [...items].sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
  } else if (knowledgeSortTab.value === 'latest') {
    items = [...items].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }
  return items
})

const selectedKnowledgeArticleText = computed(() => {
  const content = selectedKnowledgeContent.value
  if (!content) return ''
  if (content.content_type === 'article') return articleBodyByTitle[content.title] || content.description || '暂无详细内容'
  return content.description || ''
})

const progressValue = computed(() => {
  if (!totalTime.value) return 0
  return Math.min(100, Math.max(0, (currentTime.value / totalTime.value) * 100))
})

const loopModeMeta = computed(() => {
  if (loopMode.value === 'one') return { icon: Repeat1, label: '单曲循环' }
  if (loopMode.value === 'shuffle') return { icon: Shuffle, label: '随机播放' }
  return { icon: Repeat, label: '列表循环' }
})

const selectedTrackDurationSeconds = computed(() => {
  const match = selectedTrack.value.duration.match(/\d+/)
  if (!match) return 180
  return Number(match[0]) * 60
})

const formatTime = (seconds: number) => {
  const safeSeconds = Math.max(0, Math.floor(seconds || 0))
  const minutes = Math.floor(safeSeconds / 60)
  const rest = safeSeconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

const showToast = (message: string, tone: 'success' | 'error' | 'info' = 'info', duration = 1600) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const clearMessages = () => {
  toastMessage.value = ''
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
    toastTimer = null
  }
}

const loadFavorites = async () => {
  if (!authState.user) return
  try {
    const favorites = await getUserFavorites(authState.user.id)
    favoriteContentIds.value = new Set(favorites.map((item: any) => String(item.content_id)))
  } catch {
    favoriteContentIds.value = new Set()
  }
}

const loadHealingContents = async () => {
  try {
    healingContents.value = mergeLocalHealingContents(await getHealingContents())
    generateMissingVideoThumbnails()
    if (activeTab.value === 'knowledge' && interventionTargetRefId.value) {
      const target = healingContents.value.find((item) => item.id === interventionTargetRefId.value)
      if (target) void openKnowledgeDetail(target)
    }
  } catch (error) {
    healingContents.value = mergeLocalHealingContents([])
    showToast(error instanceof Error ? error.message : '加载疗愈内容失败', 'error')
  }
}

const toggleKnowledgeFavorite = async (contentId: string) => {
  clearMessages()
  if (!authState.user) {
    showToast('请先登录', 'error')
    return
  }
  if (favoriteSavingId.value) return

  favoriteSavingId.value = contentId
  try {
    const favorited = await toggleFavorite(authState.user.id, contentId)
    const next = new Set(favoriteContentIds.value)
    if (favorited) next.add(contentId)
    else next.delete(contentId)
    favoriteContentIds.value = next
    showToast(favorited ? '已添加到收藏' : '已取消收藏', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '收藏失败', 'error')
  } finally {
    favoriteSavingId.value = ''
  }
}

const formatKnowledgeCount = (count?: number | null) => {
  const safe = Number(count || 0)
  return safe >= 1000 ? `${(safe / 1000).toFixed(1)}k` : String(safe)
}

const formatTimeAgo = (dateString?: string | null) => {
  if (!dateString) return '刚刚'
  const date = new Date(dateString)
  const diffMs = Date.now() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (Number.isNaN(date.getTime()) || diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return date.toLocaleDateString('zh-CN')
}

const knowledgeTypeLabel = (type: string) => (type === 'video' ? '视频' : '文章')

const openKnowledgeDetail = async (content: HealingContent) => {
  selectedKnowledgeContent.value = normalizeHealingContent(content)
  knowledgeDetailOpen.value = true
  knowledgeShareDialogOpen.value = false
  knowledgeVideoError.value = ''
  try {
    await incrementViewCount(content.id)
    healingContents.value = healingContents.value.map((item) =>
      item.id === content.id ? { ...item, view_count: (item.view_count || 0) + 1 } : item,
    )
    if (selectedKnowledgeContent.value?.id === content.id) {
      selectedKnowledgeContent.value = {
        ...selectedKnowledgeContent.value,
        view_count: (selectedKnowledgeContent.value.view_count || 0) + 1,
      }
    }
  } catch {
    // xinyu-care detail view treats view count increment as non-blocking.
  }
}

const copyKnowledgeLink = async () => {
  const content = selectedKnowledgeContent.value
  if (!content) return
  try {
    const base = `${window.location.origin}${publicBaseUrl}`.replace(/\/?$/, '/')
    await navigator.clipboard.writeText(`${base}healing/knowledge/${content.id}`)
    showToast('链接已复制到剪贴板', 'success')
    knowledgeShareDialogOpen.value = false
  } catch {
    showToast('复制失败', 'error')
  }
}

const shiftDiaryMonth = (offset: number) => {
  diaryMonthCursor.value = new Date(diaryMonthCursor.value.getFullYear(), diaryMonthCursor.value.getMonth() + offset, 1)
}

const syncDiaryEditor = (diary: DiaryEntry | null) => {
  if (!diary) {
    diaryMood.value = 'neutral'
    diaryContent.value = ''
    diaryTriggers.value = []
    diaryImages.value = []
    diaryPositiveExtra.value = []
    diaryNegativeExtra.value = []
    return
  }
  diaryMood.value = diary.mood
  diaryContent.value = diary.content
  diaryTriggers.value = [...diary.triggers]
  diaryImages.value = [...diary.images]
  diaryPositiveExtra.value = diary.triggers.filter((tag) => !positiveTriggerSet.has(tag) && !negativeTriggerSet.has(tag))
  diaryNegativeExtra.value = []
}

const selectDiaryDate = (date: Date) => {
  diarySelectedDate.value = date
  clearMessages()
  syncDiaryEditor(diariesByDate.value.get(dateKey(date))?.[0] || null)
}

const toggleDiaryTrigger = (trigger: string) => {
  diaryTriggers.value = diaryTriggers.value.includes(trigger)
    ? diaryTriggers.value.filter((item) => item !== trigger)
    : [...diaryTriggers.value, trigger]
}

const addDiaryTrigger = (bucket: 'positive' | 'negative') => {
  const source = bucket === 'positive' ? diaryNewPositiveTag : diaryNewNegativeTag
  const extra = bucket === 'positive' ? diaryPositiveExtra : diaryNegativeExtra
  const normalized = source.value.trim()
  if (!normalized) return
  if (!extra.value.includes(normalized)) extra.value = [...extra.value, normalized]
  if (!diaryTriggers.value.includes(normalized)) diaryTriggers.value = [...diaryTriggers.value, normalized]
  source.value = ''
}

const removeDiaryTag = (tag: string) => {
  diaryTriggers.value = diaryTriggers.value.filter((item) => item !== tag)
  diaryPositiveExtra.value = diaryPositiveExtra.value.filter((item) => item !== tag)
  diaryNegativeExtra.value = diaryNegativeExtra.value.filter((item) => item !== tag)
}

const removeDiaryImage = (index: number) => {
  diaryImages.value = diaryImages.value.filter((_, currentIndex) => currentIndex !== index)
}

const handleDiaryImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement | null
  const files = target?.files
  if (!files?.length) return
  clearMessages()
  try {
    let hadError = false
    for (const file of Array.from(files)) {
      if (file.size > 10 * 1024 * 1024) {
        hadError = true
        showToast(`${file.name} 超过10MB`, 'error')
        continue
      }
      const base64 = await blobToBase64(file)
      diaryImages.value = [...diaryImages.value, `data:${file.type || 'image/png'};base64,${base64}`]
    }
    if (!hadError) showToast('图片已加入当前日记', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '图片处理失败', 'error')
  } finally {
    if (target) target.value = ''
  }
}

const resetDiaryForm = () => {
  syncDiaryEditor(null)
  clearMessages()
}

const inferAudioFormat = (blob: Blob): 'wav' | 'm4a' | 'webm' | 'ogg' | 'mp3' => {
  const type = blob.type.toLowerCase()
  if (type.includes('webm')) return 'webm'
  if (type.includes('ogg')) return 'ogg'
  if (type.includes('mpeg') || type.includes('mp3')) return 'mp3'
  if (type.includes('mp4') || type.includes('m4a')) return 'm4a'
  return 'wav'
}

const appendDiaryVoiceText = (text: string) => {
  const normalized = text.trim()
  if (!normalized) return
  diaryContent.value = diaryContent.value ? `${diaryContent.value}\n${normalized}` : normalized
}

const transcribeDiaryAudio = async (blob: Blob) => {
  diaryRecognizing.value = true
  clearMessages()
  try {
    const shouldConvertToWav = /webm|ogg|opus/i.test(blob.type || '')
    const audioBlob = shouldConvertToWav ? await convertWebmToWav(blob) : blob
    const base64 = await blobToBase64(audioBlob)
    const result = await speechRecognition(base64, inferAudioFormat(audioBlob), 16000, audioBlob.size)
    const text = String(result?.text || result?.result?.[0] || '').trim()
    if (!text) throw new Error('语音服务未返回转写文本')
    appendDiaryVoiceText(text)
    showToast('语音识别完成', 'success')
  } catch (error) {
    showToast(error instanceof Error ? `语音识别失败：${error.message}` : '语音识别失败', 'error')
  } finally {
    diaryRecognizing.value = false
  }
}

const stopDiaryVoiceStream = () => {
  diaryVoiceStream?.getTracks().forEach((track) => track.stop())
  diaryVoiceStream = null
}

const startDiaryRecording = async () => {
  clearMessages()
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    showToast('当前页面无法开启麦克风，请使用 HTTPS 访问或上传文字记录。', 'error')
    return
  }
  try {
    diaryVoiceStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    diaryAudioChunks = []
    diaryMediaRecorder = new MediaRecorder(diaryVoiceStream)
    diaryMediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) diaryAudioChunks.push(event.data)
    }
    diaryMediaRecorder.onstop = () => {
      const type = diaryAudioChunks[0]?.type || 'audio/webm'
      void transcribeDiaryAudio(new Blob(diaryAudioChunks, { type }))
      stopDiaryVoiceStream()
    }
    diaryMediaRecorder.start()
    diaryRecording.value = true
    showToast('开始录音...', 'info')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '无法访问麦克风', 'error')
    stopDiaryVoiceStream()
  }
}

const stopDiaryRecording = () => {
  if (!diaryMediaRecorder || diaryMediaRecorder.state === 'inactive') return
  diaryRecording.value = false
  diaryMediaRecorder.stop()
}

const saveDiaryEntry = async () => {
  if (!authState.user) {
    showToast('请先登录', 'error')
    return
  }
  diarySaving.value = true
  clearMessages()
  try {
    const existing = selectedDateDiary.value
    const payload = {
      emotion_level: diaryMood.value,
      content: diaryContent.value,
      tags: diaryTriggers.value,
      image_urls: diaryImages.value,
    }
    if (existing) {
      await updateEmotionDiary(existing.id, payload)
      if (isInterventionMode.value) {
        await completeCurrentIntervention({
          source_ref_table: 'emotion_diaries',
          source_ref_id: existing.id,
          duration_seconds: 0,
          summary_json: { mood: diaryMood.value, triggerCount: diaryTriggers.value.length },
        })
      }
      showToast('日记已更新', 'success')
    } else {
      const saved = await createEmotionRecord({
        date: diarySelectedDateKey.value,
        mood: diaryMood.value,
        content: diaryContent.value,
        triggers: diaryTriggers.value,
        images: diaryImages.value,
      })
      if (isInterventionMode.value && saved) {
        await completeCurrentIntervention({
          source_ref_table: 'emotion_diaries',
          source_ref_id: saved.id,
          duration_seconds: 0,
          summary_json: { mood: diaryMood.value, triggerCount: diaryTriggers.value.length },
        })
      }
      showToast('日记已保存', 'success')
      if (diaryMood.value === 'bad' || diaryMood.value === 'very_bad') diaryFeedbackType.value = 'receiver'
      else if (diaryMood.value === 'good' || diaryMood.value === 'very_good') diaryFeedbackType.value = 'giver'
    }
    await loadEmotionRecords()
  } catch (error) {
    showToast(error instanceof Error ? `保存失败：${error.message}` : '保存失败，请检查网络连接', 'error')
  } finally {
    diarySaving.value = false
  }
}

const closeKnowledgeDetail = () => {
  knowledgeDetailOpen.value = false
  knowledgeShareDialogOpen.value = false
  knowledgeVideoError.value = ''
  selectedKnowledgeContent.value = null
}

const likeKnowledgeContent = async (content: HealingContent) => {
  clearMessages()
  if (!authState.user) {
    showToast('请先登录', 'error')
    return
  }
  try {
    await incrementLikeCount(content.id)
    healingContents.value = healingContents.value.map((item) =>
      item.id === content.id ? { ...item, like_count: (item.like_count || 0) + 1 } : item,
    )
    if (selectedKnowledgeContent.value?.id === content.id) {
      selectedKnowledgeContent.value = {
        ...selectedKnowledgeContent.value,
        like_count: (selectedKnowledgeContent.value.like_count || 0) + 1,
      }
    }
    showToast('点赞成功', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '点赞失败', 'error')
  }
}

const nextTrack = () => {
  if (!meditationTracks.length) return
  if (loopMode.value === 'shuffle' && meditationTracks.length > 1) {
    const currentIndex = meditationTracks.findIndex((item) => item.id === selectedTrack.value.id)
    let candidate = currentIndex
    while (candidate === currentIndex) {
      candidate = Math.floor(Math.random() * meditationTracks.length)
    }
    selectedTrackId.value = meditationTracks[candidate]!.id
    return
  }
  const currentIndex = meditationTracks.findIndex((item) => item.id === selectedTrack.value.id)
  const nextIndex = (currentIndex + 1) % meditationTracks.length
  selectedTrackId.value = meditationTracks[nextIndex]!.id
}

const prevTrack = () => {
  if (!meditationTracks.length) return
  const currentIndex = meditationTracks.findIndex((item) => item.id === selectedTrack.value.id)
  const prevIndex = (currentIndex - 1 + meditationTracks.length) % meditationTracks.length
  selectedTrackId.value = meditationTracks[prevIndex]!.id
}

const cycleLoopMode = () => {
  loopMode.value = loopMode.value === 'all' ? 'one' : loopMode.value === 'one' ? 'shuffle' : 'all'
}

const togglePlay = async () => {
  const audio = audioRef.value
  if (!audio) return
  playError.value = ''
  try {
    if (audio.paused) {
      await audio.play()
    } else {
      audio.pause()
    }
  } catch {
    playError.value = '播放被浏览器阻止或音频暂不可用，请稍后重试。'
  }
}

const toggleMute = () => {
  muted.value = !muted.value
}

const seekByPercent = (event: Event) => {
  const audio = audioRef.value
  if (!audio || !totalTime.value) return
  const value = Number((event.target as HTMLInputElement).value)
  audio.currentTime = Math.floor((value / 100) * totalTime.value)
}

const loadStats = async () => {
  if (!authState.user) return
  loadingStats.value = true
  try {
    const stats = await getMeditationStats(authState.user.id)
    meditationStats.value = {
      totalMinutes: stats.totalMinutes ?? 0,
      totalSessions: stats.totalSessions ?? 0,
    }
  } finally {
    loadingStats.value = false
  }
}

const openCompletionDialog = () => {
  const contentId = trackContentIds[selectedTrack.value.id]
  if (!contentId) {
    showToast('当前冥想内容缺少保存映射', 'error')
    return
  }
  audioRef.value?.pause()
  clearMessages()
  completedSession.value = {
    contentId,
    title: selectedTrack.value.title,
    duration: Math.max(60, currentTime.value || totalTime.value || selectedTrackDurationSeconds.value),
  }
  moodAfter.value = 'calmer'
  sessionNotes.value = ''
  moodDialogOpen.value = true
}

const closeCompletionDialog = () => {
  moodDialogOpen.value = false
  completedSession.value = null
}

const saveMeditationSession = async () => {
  if (!authState.user || !completedSession.value) return
  savingSession.value = true
  clearMessages()
  try {
    const session = await createMeditationSession({
      user_id: authState.user.id,
      content_id: completedSession.value.contentId,
      duration: Math.max(60, completedSession.value.duration),
      completed: true,
      mood_after: moodAfter.value,
      notes: sessionNotes.value.trim() || undefined,
    })
    if (isInterventionMode.value) {
      await completeCurrentIntervention({
        source_ref_table: 'meditation_sessions',
        source_ref_id: (session as any)?.id,
        duration_seconds: Math.max(10, Number(route.query.duration || 10)),
        summary_json: {
          title: completedSession.value.title,
          moodAfter: moodAfter.value,
        },
      })
    }
    await loadStats()
    showToast('冥想记录已保存', 'success')
    closeCompletionDialog()
    currentTime.value = 0
  } finally {
    savingSession.value = false
  }
}

const loadSelectedTrack = () => {
  const audio = audioRef.value
  const track = selectedTrack.value
  if (!audio || !track) return
  audio.src = publicAssetUrl(track.audio)
  audio.volume = muted.value ? 0 : volume.value
  audio.load()
  currentTime.value = 0
  totalTime.value = 0
  buffering.value = false
  isPlaying.value = false
}

watch(
  selectedTrack,
  () => loadSelectedTrack(),
  { immediate: true },
)

watch([volume, muted], () => {
  const audio = audioRef.value
  if (!audio) return
  audio.volume = muted.value ? 0 : volume.value
})

onMounted(() => {
  startInterventionCountdown()
  void loadStats()
  void loadHealingContents()
  void loadFavorites()
  void loadEmotionRecords().then(() => {
    syncDiaryEditor(selectedDateDiary.value)
  })

  const audio = audioRef.value
  if (!audio) return

  const onLoadedMetadata = () => {
    totalTime.value = Math.floor(audio.duration || 0)
  }
  const onTimeUpdate = () => {
    currentTime.value = Math.floor(audio.currentTime || 0)
  }
  const onPlay = () => {
    isPlaying.value = true
  }
  const onPause = () => {
    isPlaying.value = false
  }
  const onWaiting = () => {
    buffering.value = true
  }
  const onPlaying = () => {
    buffering.value = false
  }
  const onEnded = () => {
    buffering.value = false
    isPlaying.value = false
    openCompletionDialog()
    if (loopMode.value === 'one') {
      audio.currentTime = 0
    }
  }
  const onError = () => {
    buffering.value = false
    isPlaying.value = false
    playError.value = '当前音频加载失败，已为你切换下一首。'
    nextTrack()
  }

  audio.addEventListener('loadedmetadata', onLoadedMetadata)
  audio.addEventListener('timeupdate', onTimeUpdate)
  audio.addEventListener('play', onPlay)
  audio.addEventListener('pause', onPause)
  audio.addEventListener('waiting', onWaiting)
  audio.addEventListener('playing', onPlaying)
  audio.addEventListener('ended', onEnded)
  audio.addEventListener('error', onError)

  loadSelectedTrack()

  cleanupAudioListeners = () => {
    audio.pause()
    audio.removeEventListener('loadedmetadata', onLoadedMetadata)
    audio.removeEventListener('timeupdate', onTimeUpdate)
    audio.removeEventListener('play', onPlay)
    audio.removeEventListener('pause', onPause)
    audio.removeEventListener('waiting', onWaiting)
    audio.removeEventListener('playing', onPlaying)
    audio.removeEventListener('ended', onEnded)
    audio.removeEventListener('error', onError)
  }
})

onBeforeUnmount(() => {
  cleanupAudioListeners?.()
  clearInterventionTimer()
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  if (diaryRecording.value) {
    stopDiaryRecording()
  } else {
    stopDiaryVoiceStream()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 py-4 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/20 md:py-6">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : toastTone === 'success' ? 'bg-emerald-600 shadow-emerald-900/20' : 'bg-slate-950 shadow-slate-900/20'"
      data-testid="healing-toast"
    >
      {{ toastMessage }}
    </div>
    <div class="mx-auto w-full max-w-6xl px-4 md:px-6">
    <audio ref="audioRef" class="hidden" preload="auto" />

    <div class="mt-6 grid grid-cols-4 gap-2 md:gap-3">
      <button
        v-for="item in tabs"
        :key="item.key"
        :data-testid="`healing-tab-${item.key}`"
        class="rounded-2xl px-4 py-4 text-sm font-semibold transition"
        :class="
          activeTab === item.key
            ? 'bg-slate-900 text-white shadow-lg dark:bg-white dark:text-slate-900'
            : 'bg-white text-slate-500 shadow-sm dark:bg-slate-900 dark:text-slate-300'
        "
        @click="activeTab = item.key"
      >
        <span class="inline-flex items-center gap-2">
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </span>
      </button>
    </div>

    <div v-if="isInterventionMode" class="mt-4 rounded-[24px] border border-emerald-100 bg-emerald-50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/20">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-sm font-black text-emerald-800 dark:text-emerald-100">当前干预任务中</p>
          <p class="mt-1 text-xs leading-5 text-emerald-700/80 dark:text-emerald-200/80">
            {{ interventionCompleted ? '今日已完成，可继续自由练习。' : canCompleteIntervention ? '倒计时已结束，可以在本页面记录完成。' : `请在当前页面停留 ${interventionRemaining} 秒后完成。` }}
          </p>
        </div>
        <button class="rounded-xl bg-white px-4 py-2 text-xs font-black text-emerald-700 shadow-sm dark:bg-slate-950 dark:text-emerald-200" type="button" @click="router.push(interventionReturnTo)">
          返回任务中心
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'meditation'" class="mt-6 grid gap-6 md:grid-cols-2 md:items-start">
      <BaseCard class="order-2 overflow-hidden">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg">
            <Music class="h-6 w-6" />
          </div>
          <div>
            <h2 class="text-xl font-bold text-slate-900 dark:text-white">冥想库</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400">探索内心的宁静</p>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-2 gap-2">
          <button
            v-for="item in categoryMeta"
            :key="item.key"
            class="rounded-[20px] p-3 text-left text-sm transition"
            :class="activeCategory === item.key ? `bg-gradient-to-br ${item.tone} text-white shadow-lg` : 'bg-slate-50 text-slate-600 dark:bg-slate-900 dark:text-slate-300'"
            @click="activeCategory = item.key"
          >
            <component :is="item.icon" class="mb-2 h-4 w-4" />
            {{ item.label }}
          </button>
        </div>

        <div class="mt-5 space-y-3">
          <button
            v-for="item in filteredTracks"
            :key="item.id"
            class="w-full rounded-[24px] p-4 text-left transition"
            :class="selectedTrackId === item.id ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-300'"
            @click="selectedTrackId = item.id"
          >
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ item.emoji }}</span>
              <div>
                <p class="font-semibold">{{ item.title }}</p>
                <p class="text-xs opacity-70">{{ item.category }} · {{ item.duration }}</p>
              </div>
            </div>
          </button>
        </div>
      </BaseCard>

      <div class="order-1 space-y-6 md:sticky md:top-6">
        <BaseCard class="overflow-hidden border-0 bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-white">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <span class="rounded-full bg-white/10 px-4 py-2 text-xs font-semibold text-indigo-100 backdrop-blur">
              {{ buffering ? '缓冲中' : isPlaying ? '正在播放' : '已暂停' }}
            </span>
            <span class="rounded-full bg-white/10 px-4 py-2 text-xs text-white/70">{{ loopModeMeta.label }}</span>
          </div>
          <h3 class="mt-3 text-3xl font-bold">{{ selectedTrack.title }}</h3>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-white/75">{{ selectedTrack.description }}</p>

          <div v-if="playError" class="mt-4 rounded-[20px] border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
            {{ playError }}
          </div>

          <div class="mt-6 flex items-center justify-center">
            <div class="relative flex h-32 w-32 items-center justify-center rounded-full bg-white/10 text-5xl backdrop-blur md:h-40 md:w-40">
              <span
                class="absolute inset-0 rounded-full border border-indigo-300/30"
                :class="isPlaying ? 'animate-ping' : ''"
              />
              <span class="relative">{{ selectedTrack.emoji }}</span>
            </div>
          </div>

          <div class="mt-6">
            <div class="mb-2 flex items-center justify-between text-xs text-white/60">
              <span>{{ formatTime(currentTime) }}</span>
              <span>{{ formatTime(totalTime || selectedTrackDurationSeconds) }}</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-white/10">
              <div class="h-full rounded-full bg-gradient-to-r from-indigo-400 to-fuchsia-400 transition-all" :style="{ width: `${progressValue}%` }" />
            </div>
            <input
              class="mt-3 h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-violet-300"
              data-testid="healing-progress-slider"
              max="100"
              min="0"
              type="range"
              :value="progressValue"
              @input="seekByPercent"
            />
          </div>

          <div class="mt-6 flex items-center justify-center gap-3 md:gap-4">
            <button
              class="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white/75 transition hover:bg-white/20 hover:text-white"
              data-testid="healing-loop-mode"
              type="button"
              @click="cycleLoopMode"
            >
              <component :is="loopModeMeta.icon" class="h-5 w-5" />
            </button>
            <button class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20" type="button" @click="prevTrack">
              <SkipBack class="h-5 w-5" />
            </button>
            <button class="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/40" data-testid="healing-toggle-play" type="button" @click="togglePlay">
              <span v-if="buffering" class="h-7 w-7 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              <Pause v-else-if="isPlaying" class="h-7 w-7" />
              <Play v-else class="h-7 w-7 translate-x-0.5" />
            </button>
            <button class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20" type="button" @click="nextTrack">
              <SkipForward class="h-5 w-5" />
            </button>
            <button
              class="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white/75 transition hover:bg-white/20 hover:text-white"
              data-testid="healing-mute-toggle"
              type="button"
              @click="toggleMute"
            >
              <VolumeX v-if="muted" class="h-5 w-5" />
              <Volume2 v-else class="h-5 w-5" />
            </button>
          </div>

          <div class="mt-5 flex items-center gap-3 rounded-[22px] bg-white/10 px-4 py-3">
            <Volume2 class="h-4 w-4 text-white/60" />
            <input
              v-model.number="volume"
              class="h-2 flex-1 cursor-pointer appearance-none rounded-full bg-white/15 accent-violet-300"
              data-testid="healing-volume-slider"
              max="1"
              min="0"
              step="0.05"
              type="range"
            />
            <span class="w-10 text-right text-xs text-white/60">{{ Math.round(volume * 100) }}%</span>
          </div>

          <button
            class="mt-6 w-full rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 disabled:opacity-60"
            :disabled="savingSession || !authState.user || (isInterventionMode && !canCompleteIntervention)"
            data-testid="healing-save-session"
            type="button"
            @click="openCompletionDialog"
          >
            {{ isInterventionMode && !canCompleteIntervention ? `${interventionRemaining} 秒后可记录完成` : '记录本次冥想完成' }}
          </button>
        </BaseCard>

        <div class="hidden grid-cols-3 gap-3 md:grid">
          <BaseCard class="p-4 text-center shadow-sm">
            <div class="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
              <Clock3 class="h-5 w-5" />
            </div>
            <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ loadingStats ? '...' : meditationStats.totalMinutes }}</p>
            <p class="text-xs text-slate-500">冥想分钟</p>
          </BaseCard>
          <BaseCard class="p-4 text-center shadow-sm">
            <div class="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white">
              <Target class="h-5 w-5" />
            </div>
            <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ loadingStats ? '...' : meditationStats.totalSessions }}</p>
            <p class="text-xs text-slate-500">完成次数</p>
          </BaseCard>
          <BaseCard class="p-4 text-center shadow-sm">
            <div class="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 text-white">
              <Flame class="h-5 w-5" />
            </div>
            <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ Math.min(7, meditationStats.totalSessions) }}</p>
            <p class="text-xs text-slate-500">连续天数</p>
          </BaseCard>
        </div>

        <BaseCard class="hidden p-5 shadow-sm md:block">
          <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                <Trophy class="h-4 w-4" />
              </div>
              <span class="font-semibold text-slate-900 dark:text-white">本周目标</span>
            </div>
            <span class="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
              {{ Math.min(100, Math.round((meditationStats.totalSessions / 7) * 100)) }}%
            </span>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm text-slate-500">
              <span>已完成 {{ meditationStats.totalSessions }} 次</span>
              <span>目标 7 次</span>
            </div>
            <div class="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all" :style="{ width: `${Math.min(100, (meditationStats.totalSessions / 7) * 100)}%` }" />
            </div>
          </div>
          <div class="mt-4 flex items-center gap-2 text-xs text-slate-500">
            <Star class="h-3 w-3 fill-current text-amber-500" />
            <span>坚持冥想有助于改善睡眠质量和情绪管理</span>
          </div>
        </BaseCard>

        <BaseCard class="hidden p-5 shadow-sm md:block">
          <div class="mb-4 flex items-center gap-2">
            <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-rose-500 to-pink-600 text-white">
              <TrendingUp class="h-4 w-4" />
            </div>
            <span class="font-semibold text-slate-900 dark:text-white">为你推荐</span>
          </div>
          <div class="space-y-3">
            <button
              v-for="(track, index) in meditationTracks.slice(0, 2)"
              :key="track.id"
              class="flex w-full items-center gap-3 rounded-xl bg-slate-100/70 p-3 text-left transition hover:translate-x-1 hover:bg-slate-100 dark:bg-slate-900 dark:hover:bg-slate-800"
              type="button"
              @click="selectedTrackId = track.id"
            >
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-2xl" :class="track.cover">
                {{ track.emoji }}
              </div>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-slate-900 dark:text-white">{{ track.title }}</p>
                <p class="truncate text-xs text-slate-500">{{ track.description }}</p>
              </div>
              <span class="flex h-6 w-6 items-center justify-center rounded-full bg-rose-100 text-xs font-bold text-rose-600 dark:bg-rose-900/30 dark:text-rose-300">
                {{ index + 1 }}
              </span>
            </button>
          </div>
        </BaseCard>
      </div>
    </div>

    <div v-else-if="activeTab === 'diary'" class="mt-6 grid gap-6 lg:grid-cols-2" data-testid="healing-diary-panel">
      <div class="space-y-4 lg:sticky lg:top-6 lg:self-start">
        <BaseCard class="overflow-hidden border-0 shadow-xl">
          <div class="flex items-center justify-between gap-3">
            <h2 class="flex items-center gap-2 text-lg font-black text-slate-900 dark:text-white">
              <Sparkles class="h-5 w-5 text-primary" />
              情绪日历
            </h2>
            <div class="flex items-center gap-2">
              <button class="grid h-8 w-8 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="healing-diary-prev-month" type="button" @click="shiftDiaryMonth(-1)">
                <ChevronLeft class="h-4 w-4" />
              </button>
              <span class="min-w-24 text-center text-sm font-semibold text-slate-600 dark:text-slate-300">{{ diaryMonthLabel }}</span>
              <button class="grid h-8 w-8 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="healing-diary-next-month" type="button" @click="shiftDiaryMonth(1)">
                <ChevronRight class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="mt-4 grid grid-cols-7 gap-1 text-center text-xs text-slate-400">
            <span v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="py-2">{{ day }}</span>
          </div>
          <div class="grid grid-cols-7 gap-1" data-testid="healing-diary-calendar">
            <div v-for="(date, index) in diaryCalendarDays" :key="date ? date.toISOString() : `empty-${index}`" class="aspect-square">
              <button
                v-if="date"
                class="relative flex h-full w-full flex-col items-center justify-center gap-1 rounded-xl border text-sm font-semibold transition hover:scale-[1.03]"
                :class="[
                  dateKey(date) === dateKey(new Date()) ? 'ring-2 ring-primary ring-offset-2 dark:ring-offset-slate-950' : '',
                  dateKey(date) === diarySelectedDateKey ? 'border-primary bg-primary/10 text-primary' : 'border-transparent bg-slate-100/70 text-slate-600 dark:bg-slate-900 dark:text-slate-300',
                  diariesByDate.get(dateKey(date))?.[0] ? moodMeta[diariesByDate.get(dateKey(date))![0]!.mood].tone : '',
                ]"
                :data-testid="`healing-diary-day-${dateKey(date)}`"
                type="button"
                @click="selectDiaryDate(date)"
              >
                <span>{{ date.getDate() }}</span>
                <span v-if="diariesByDate.get(dateKey(date))?.[0]" class="text-lg">{{ moodMeta[diariesByDate.get(dateKey(date))![0]!.mood].emoji }}</span>
              </button>
            </div>
          </div>
        </BaseCard>

        <div class="hidden grid-cols-3 gap-3 lg:grid">
          <BaseCard class="p-3 text-center">
            <div class="mx-auto mb-1 grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-rose-500 to-pink-600 text-white">
              <CalendarDays class="h-4 w-4" />
            </div>
            <p class="text-lg font-black text-slate-900 dark:text-white">{{ diaryInsights.latestCount }}</p>
            <p class="text-xs text-slate-400">日记总数</p>
          </BaseCard>
          <BaseCard class="p-3 text-center">
            <div class="mx-auto mb-1 grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 text-white">
              <PenLine class="h-4 w-4" />
            </div>
            <p class="text-lg font-black text-slate-900 dark:text-white">{{ Math.min(7, diaryInsights.weeklyCount) }}</p>
            <p class="text-xs text-slate-400">本周记录</p>
          </BaseCard>
          <BaseCard class="p-3 text-center">
            <div class="mx-auto mb-1 grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
              <Heart class="h-4 w-4" />
            </div>
            <p class="text-lg font-black text-slate-900 dark:text-white">{{ diaryInsights.positivePercent }}%</p>
            <p class="text-xs text-slate-400">积极情绪</p>
          </BaseCard>
        </div>

        <BaseCard class="hidden lg:block">
          <div class="mb-4 flex items-center gap-2">
            <div class="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white">
              <TrendingUp class="h-4 w-4" />
            </div>
            <span class="font-bold text-slate-900 dark:text-white">心情趋势</span>
          </div>
          <div class="space-y-3">
            <div v-for="item in diaryMoodTrend" :key="item.key" class="flex items-center gap-3">
              <span class="w-6 text-lg">{{ item.emoji }}</span>
              <span class="w-10 text-xs text-slate-500">{{ item.label }}</span>
              <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-900">
                <div class="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500" :style="{ width: item.width }" />
              </div>
              <span class="w-6 text-right text-xs font-semibold">{{ item.count }}</span>
            </div>
          </div>
        </BaseCard>

        <BaseCard class="hidden lg:block">
          <div class="mb-4 flex items-center gap-2">
            <div class="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-sky-500 to-cyan-600 text-white">
              <Target class="h-4 w-4" />
            </div>
            <span class="font-bold text-slate-900 dark:text-white">常用标签</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="item in commonDiaryTags"
              :key="item.tag"
              class="rounded-full px-3 py-1.5 text-xs font-semibold"
              :class="item.positive ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300'"
            >
              {{ item.tag }} <span class="opacity-60">{{ item.count }}</span>
            </span>
          </div>
        </BaseCard>

        <BaseCard class="hidden lg:block">
          <div class="flex items-start gap-3">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 text-white">
              <Smile class="h-5 w-5" />
            </div>
            <div>
              <p class="font-semibold text-slate-900 dark:text-white">每日小贴士</p>
              <p class="mt-1 text-sm leading-6 text-slate-500">记录情绪是自我关怀的第一步。坚持写日记可以帮助你发现情绪模式，更好地了解自己。</p>
            </div>
          </div>
        </BaseCard>
      </div>

      <BaseCard class="overflow-hidden border-0 shadow-xl">
        <div class="flex items-center justify-between gap-3">
          <h2 class="flex items-center gap-2 text-lg font-black text-slate-900 dark:text-white">
            <PenLine class="h-5 w-5 text-primary" />
            {{ selectedDateDiary ? '编辑日记' : '写日记' }} - {{ diarySelectedDateLabel }}
          </h2>
          <button class="inline-flex items-center gap-1 rounded-full px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="healing-diary-reset" type="button" @click="resetDiaryForm">
            <X class="h-4 w-4" />
            重置
          </button>
        </div>

        <div class="mt-6 space-y-6">
          <div class="space-y-3">
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">今天感觉如何？</p>
            <div class="grid grid-cols-5 gap-2">
              <button
                v-for="[key, meta] in moodEntries"
                :key="key"
                class="flex min-h-20 flex-col items-center justify-center gap-1 rounded-xl border-2 p-2 transition hover:scale-[1.03]"
                :class="diaryMood === key ? `${meta.tone} border-primary/40 shadow-sm` : 'border-slate-100 bg-slate-50 text-slate-500 dark:border-slate-800 dark:bg-slate-900'"
                :data-testid="`healing-diary-mood-${key}`"
                type="button"
                @click="diaryMood = key"
              >
                <span class="text-2xl">{{ meta.emoji }}</span>
                <span class="text-xs font-semibold">{{ meta.label }}</span>
              </button>
            </div>
          </div>

          <div class="space-y-4">
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">是什么影响了你的情绪？</p>
            <div class="space-y-2">
              <p class="text-xs text-slate-400">积极因素</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="trigger in positiveTriggers"
                  :key="trigger"
                  class="inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs font-semibold transition"
                  :class="diaryTriggers.includes(trigger) ? 'border-emerald-300 bg-emerald-100 text-emerald-700' : 'border-slate-200 text-slate-500 dark:border-slate-800'"
                  type="button"
                  @click="toggleDiaryTrigger(trigger)"
                >
                  <Sun class="h-3 w-3" />
                  {{ trigger }}
                </button>
                <button
                  v-for="tag in diaryPositiveExtra"
                  :key="tag"
                  class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-semibold text-emerald-700"
                  type="button"
                  @click="removeDiaryTag(tag)"
                >
                  {{ tag }} <X class="h-3 w-3" />
                </button>
              </div>
              <div class="flex gap-2">
                <input v-model="diaryNewPositiveTag" class="h-10 flex-1 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-950" data-testid="healing-diary-positive-input" placeholder="添加自定义标签..." @keydown.enter.prevent="addDiaryTrigger('positive')" />
                <button class="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 dark:border-slate-800" data-testid="healing-diary-positive-add" type="button" @click="addDiaryTrigger('positive')">
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            </div>

            <div class="space-y-2">
              <p class="text-xs text-slate-400">消极因素</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="trigger in negativeTriggers"
                  :key="trigger"
                  class="inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs font-semibold transition"
                  :class="diaryTriggers.includes(trigger) ? 'border-rose-300 bg-rose-100 text-rose-700' : 'border-slate-200 text-slate-500 dark:border-slate-800'"
                  type="button"
                  @click="toggleDiaryTrigger(trigger)"
                >
                  <CloudRain class="h-3 w-3" />
                  {{ trigger }}
                </button>
                <button
                  v-for="tag in diaryNegativeExtra"
                  :key="tag"
                  class="inline-flex items-center gap-1 rounded-full bg-rose-100 px-3 py-1.5 text-xs font-semibold text-rose-700"
                  type="button"
                  @click="removeDiaryTag(tag)"
                >
                  {{ tag }} <X class="h-3 w-3" />
                </button>
              </div>
              <div class="flex gap-2">
                <input v-model="diaryNewNegativeTag" class="h-10 flex-1 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-950" data-testid="healing-diary-negative-input" placeholder="添加自定义标签..." @keydown.enter.prevent="addDiaryTrigger('negative')" />
                <button class="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 dark:border-slate-800" data-testid="healing-diary-negative-add" type="button" @click="addDiaryTrigger('negative')">
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">详细记录</p>
            <div class="relative">
              <textarea
                v-model="diaryContent"
                class="min-h-36 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 pr-24 text-sm leading-6 outline-none transition focus:border-primary/50 dark:border-slate-800 dark:bg-slate-950"
                data-testid="healing-diary-content"
                placeholder="记录下今天的想法和感受..."
              />
              <div class="absolute bottom-3 right-3 flex gap-2">
                <input ref="diaryFileInput" class="hidden" data-testid="healing-diary-image-input" type="file" accept="image/*" multiple @change="handleDiaryImageUpload" />
                <button class="grid h-9 w-9 place-items-center rounded-full text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="healing-diary-image-trigger" type="button" @click="diaryFileInput?.click()">
                  <ImagePlus class="h-4 w-4" />
                </button>
                <button
                  class="grid h-9 w-9 place-items-center rounded-full text-slate-500 hover:bg-slate-100 disabled:opacity-50 dark:hover:bg-slate-900"
                  :class="diaryRecording ? 'bg-rose-100 text-rose-600' : ''"
                  :disabled="diaryRecognizing"
                  data-testid="healing-diary-voice-trigger"
                  type="button"
                  @click="diaryRecording ? stopDiaryRecording() : startDiaryRecording()"
                >
                  <LoaderCircle v-if="diaryRecognizing" class="h-4 w-4 animate-spin" />
                  <StopCircle v-else-if="diaryRecording" class="h-4 w-4" />
                  <Mic v-else class="h-4 w-4" />
                </button>
              </div>
            </div>

            <div v-if="diaryImages.length" class="flex flex-wrap gap-2" data-testid="healing-diary-images">
              <div v-for="(url, index) in diaryImages" :key="`${url}-${index}`" class="relative">
                <img alt="" class="h-20 w-20 rounded-lg object-cover" :src="url" />
                <button class="absolute -right-1 -top-1 grid h-5 w-5 place-items-center rounded-full bg-rose-500 text-white" type="button" @click="removeDiaryImage(index)">
                  <X class="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>

          <div class="flex gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
            <button class="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-600 dark:border-slate-800 dark:text-slate-300" data-testid="healing-diary-clear" type="button" @click="resetDiaryForm">
              清空
            </button>
            <button
              class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-rose-500 to-pink-600 px-4 py-3 text-sm font-bold text-white shadow-lg disabled:opacity-60"
              :disabled="diarySaving"
              data-testid="healing-diary-save"
              type="button"
              @click="saveDiaryEntry"
            >
              <LoaderCircle v-if="diarySaving" class="h-4 w-4 animate-spin" />
              <Save v-else class="h-4 w-4" />
              {{ selectedDateDiary ? '更新' : '保存' }}
            </button>
          </div>
        </div>
      </BaseCard>
    </div>

    <div v-else-if="activeTab === 'knowledge'" class="mt-6 space-y-6">
      <BaseCard class="overflow-hidden border-0 shadow-xl">
        <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/15 via-teal-500/10 to-green-500/15" />
        <div class="relative space-y-4">
          <div class="relative">
            <Search class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              v-model="knowledgeSearchQuery"
              class="h-14 w-full rounded-2xl border border-slate-200 bg-white/60 pl-12 pr-4 text-base outline-none transition focus:border-violet-300 dark:border-slate-800 dark:bg-slate-900/70"
              data-testid="healing-knowledge-search"
              placeholder="搜索内容..."
            />
          </div>
          <div class="flex gap-2 overflow-x-auto pb-2">
            <button
              v-for="item in knowledgeTypes"
              :key="item.key"
              class="inline-flex shrink-0 items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition"
              :class="knowledgeSelectedType === item.key ? `bg-gradient-to-r ${item.tone} text-white shadow-lg` : 'bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-300'"
              :data-testid="`healing-knowledge-type-${item.key}`"
              type="button"
              @click="knowledgeSelectedType = item.key"
            >
              <component :is="item.icon" class="h-4 w-4" />
              {{ item.label }}
            </button>
          </div>
        </div>
      </BaseCard>

      <div class="flex gap-3">
        <button
          v-for="item in knowledgeSortTabs"
          :key="item.key"
          class="inline-flex flex-1 items-center justify-center gap-2 rounded-full px-3 py-4 text-sm font-semibold transition"
          :class="knowledgeSortTab === item.key ? `bg-gradient-to-r ${item.tone} text-white shadow-lg` : 'bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-300'"
          :data-testid="`healing-knowledge-sort-${item.key}`"
          type="button"
          @click="knowledgeSortTab = item.key"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </button>
      </div>

      <div v-if="filteredKnowledgeContents.length === 0" class="rounded-[28px] border border-slate-100 bg-white p-12 text-center text-slate-500 dark:border-slate-800 dark:bg-slate-900">
        <Search class="mx-auto h-10 w-10 opacity-50" />
        <p class="mt-4">没有找到相关内容</p>
        <p class="mt-2 text-sm">试试其他关键词或筛选条件</p>
      </div>

      <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2" data-testid="healing-knowledge-list">
        <article
          v-for="item in filteredKnowledgeContents"
          :key="item.id"
          class="flex cursor-pointer flex-col overflow-hidden rounded-[28px] border border-slate-100 bg-white shadow-lg transition hover:-translate-y-0.5 hover:shadow-2xl dark:border-slate-800 dark:bg-slate-900"
          data-testid="healing-knowledge-item"
          @click="openKnowledgeDetail(item)"
        >
          <div v-if="item.content_type === 'video'" class="relative aspect-video overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <img v-if="knowledgeThumbnail(item)" :src="knowledgeThumbnail(item)" :alt="item.title" class="absolute inset-0 h-full w-full object-cover" data-testid="healing-knowledge-video-cover" />
            <div class="absolute inset-0 bg-black/30" />
            <div v-if="videoThumbnailLoading[item.id] && !knowledgeThumbnail(item)" class="absolute inset-0 flex items-center justify-center">
              <span class="h-8 w-8 animate-spin rounded-full border-4 border-white/30 border-t-white" />
            </div>
            <div class="absolute inset-0 flex items-center justify-center">
              <div class="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-rose-500 to-pink-600 shadow-2xl shadow-rose-500/40">
                <Play class="ml-1 h-8 w-8 fill-white text-white" />
              </div>
            </div>
          </div>

          <div class="flex flex-1 flex-col p-5">
            <div v-if="item.content_type === 'article'" class="mb-4 flex items-start justify-between gap-3">
              <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-cyan-500 shadow-lg">
                <FileText class="h-7 w-7 text-white" />
              </div>
              <span v-if="(item.view_count || 0) > 1000" class="rounded-full bg-gradient-to-r from-orange-500 to-red-500 px-3 py-1 text-xs font-semibold text-white">
                热门
              </span>
            </div>

            <h3 class="line-clamp-2 text-lg font-bold text-slate-900 dark:text-white">{{ item.title }}</h3>
            <p class="mt-3 line-clamp-4 min-h-20 flex-1 text-sm leading-6 text-slate-500">{{ item.description }}</p>

            <div class="mt-4 flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <span v-if="item.author" class="inline-flex items-center gap-1">{{ item.author }}</span>
              <span class="inline-flex items-center gap-1"><Eye class="h-3 w-3" />{{ formatKnowledgeCount(item.view_count) }}</span>
              <span v-if="item.duration" class="inline-flex items-center gap-1"><Clock3 class="h-3 w-3" />{{ Math.floor((item.duration || 0) / 60) }}分钟</span>
              <span class="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">{{ knowledgeTypeLabel(item.content_type) }}</span>
            </div>

            <div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4 dark:border-slate-800">
              <div class="flex items-center gap-3">
                <button class="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-pink-500" data-testid="healing-knowledge-like" type="button" @click.stop="likeKnowledgeContent(item)">
                  <Heart class="h-4 w-4" />
                  {{ item.like_count || 0 }}
                </button>
                <span class="inline-flex items-center gap-1 text-xs text-slate-400">
                  <Play class="h-4 w-4" />
                  {{ item.content_type === 'article' ? '阅读' : '观看' }}
                </span>
              </div>
              <button
                class="inline-flex h-9 w-9 items-center justify-center rounded-full transition"
                :aria-label="favoriteContentIds.has(item.id) ? '取消收藏' : '收藏'"
                :class="favoriteContentIds.has(item.id) ? 'bg-amber-50 text-amber-500' : 'bg-slate-100 text-slate-400 dark:bg-slate-800'"
                :disabled="favoriteSavingId === item.id"
                data-testid="healing-knowledge-favorite"
                type="button"
                @click.stop="toggleKnowledgeFavorite(item.id)"
              >
                <Bookmark class="h-4 w-4" :class="favoriteContentIds.has(item.id) ? 'fill-current' : ''" />
              </button>
            </div>
          </div>
        </article>
      </div>

      <div v-if="filteredKnowledgeContents.length > 0" class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
        <div class="mb-2 flex items-center justify-center gap-2">
          <Sparkles class="h-4 w-4 text-primary" />
          <span>持续学习,不断成长</span>
          <Sparkles class="h-4 w-4 text-primary" />
        </div>
        <p class="text-xs">已加载 {{ filteredKnowledgeContents.length }} 条内容</p>
      </div>
    </div>

    <div v-else class="relative -mx-4 mt-1 flex h-[calc(100vh-160px)] flex-col overflow-hidden rounded-b-[40px] rounded-t-[32px] border-t border-white/50 bg-gradient-to-br from-[#f8f9ff] via-[#f0f2ff] to-[#fdfaff] shadow-[0_-4px_24px_rgba(0,0,0,0.05)]">
      <div class="pointer-events-none absolute inset-x-0 top-0 h-[300px] bg-gradient-to-b from-indigo-100/40 via-transparent to-transparent" />
      <div
        class="pointer-events-none absolute inset-0 opacity-[0.4]"
        style="background-image: radial-gradient(circle at 2px 2px, #818cf8 1px, transparent 0); background-size: 32px 32px;"
      />
      <div
        class="pointer-events-none absolute inset-0 opacity-[0.2]"
        style="background-image: radial-gradient(circle at 10px 10px, #c084fc 1px, transparent 0); background-size: 48px 48px;"
      />

      <div class="relative z-10 flex flex-1 flex-col items-center space-y-4 overflow-y-auto px-5 pb-8 pt-6">
        <div class="relative">
          <div class="absolute inset-0 scale-110 rounded-full bg-orange-400/10 blur-[30px]" />
          <div class="relative h-24 w-24 overflow-hidden rounded-[28px] border-[3px] border-white shadow-lg shadow-indigo-100/50">
            <img :src="templeRunIconUrl" alt="Temple Run 2" class="h-full w-full object-cover" />
          </div>
        </div>

        <div class="space-y-1.5 text-center">
          <h1 class="text-3xl font-black tracking-normal text-slate-900">神庙逃亡 2</h1>
          <p class="text-[10px] font-bold uppercase tracking-widest text-indigo-400">Holi Festival · 跑酷闯关</p>
          <div class="flex items-center justify-center gap-2 pt-1">
            <div class="flex items-center gap-1 rounded-full border border-indigo-50 bg-white px-3 py-1 text-[10px] font-black text-indigo-600 shadow-sm">
              <Flame class="h-3 w-3 text-orange-500" />
              动作
            </div>
            <div class="flex items-center gap-1 rounded-full border border-indigo-50 bg-white px-3 py-1 text-[10px] font-black text-indigo-600 shadow-sm">
              <Zap class="h-3 w-3 text-blue-500" />
              跑酷
            </div>
            <div class="flex items-center gap-1 rounded-full border border-indigo-50 bg-white px-3 py-1 text-[10px] font-black text-indigo-600 shadow-sm">
              <Sparkles class="h-3 w-3 text-purple-500" />
              节日
            </div>
          </div>
        </div>

        <div class="w-full max-w-[280px]">
          <div class="relative">
            <div class="absolute -inset-1 rounded-[22px] bg-gradient-to-r from-pink-400 via-orange-400 to-yellow-400 opacity-30 blur-lg" />
            <button
              class="relative flex h-14 w-full items-center justify-center gap-3 rounded-[20px] bg-gradient-to-r from-pink-500 via-orange-500 to-yellow-500 shadow-lg transition active:scale-95"
              data-testid="healing-start-game"
              type="button"
              @click="openTempleRun"
            >
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 text-white ring-2 ring-white/10">
                <Play class="h-5 w-5 fill-white" />
              </div>
              <span class="text-lg font-black tracking-normal text-white">开始游戏</span>
            </button>
          </div>
          <button
            v-if="isInterventionMode"
            class="mt-3 flex h-12 w-full items-center justify-center gap-2 rounded-[18px] text-sm font-black transition"
            :class="canCompleteIntervention ? 'bg-slate-900 text-white' : 'bg-slate-200 text-slate-400'"
            :disabled="!canCompleteIntervention || interventionCompleting"
            type="button"
            @click="completeGameIntervention"
          >
            <Check class="h-4 w-4" />
            {{ interventionCompleted ? '今日已完成' : canCompleteIntervention ? '记录游戏干预完成' : `${interventionRemaining} 秒后可完成` }}
          </button>
          <p class="mt-3 text-center text-[9px] font-bold uppercase tracking-[0.15em] text-slate-400">将在浏览器中全屏运行</p>
        </div>

        <div class="w-full max-w-md space-y-3">
          <div class="space-y-2 rounded-[28px] border border-white bg-white/60 p-4 shadow-sm backdrop-blur-md">
            <div class="mb-0.5 flex items-center gap-2">
              <div class="rounded-lg bg-orange-50 p-1">
                <Gamepad2 class="h-4 w-4 text-orange-400" />
              </div>
              <h3 class="text-[12px] font-black uppercase tracking-wide text-slate-800">游戏简介</h3>
            </div>
            <p class="text-[11px] font-medium leading-relaxed text-slate-600">
              经典无尽跑酷游戏。在 Holi Festival 版本中，奔驰在五彩世界，躲避障碍跳跃，享受飞驰快感！
            </p>
          </div>

          <div class="space-y-3 rounded-[28px] border border-white bg-white/60 p-4 shadow-sm backdrop-blur-md">
            <div class="mb-0.5 flex items-center gap-2">
              <div class="rounded-lg bg-indigo-50 p-1">
                <Smartphone class="h-4 w-4 text-blue-400" />
              </div>
              <h3 class="text-[12px] font-black uppercase tracking-wide text-slate-800">操作说明</h3>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div v-for="item in gameControls" :key="item.label" class="flex items-center gap-2.5 rounded-2xl border border-indigo-50/50 bg-white/50 p-2.5">
                <div class="flex h-8 w-8 items-center justify-center rounded-xl" :class="item.tone">
                  <component :is="item.icon" class="h-4 w-4" />
                </div>
                <p class="text-[11px] font-bold text-slate-700">{{ item.label }}</p>
              </div>
            </div>
            <div class="flex items-center justify-center gap-2 rounded-xl border border-indigo-50/50 bg-indigo-50/30 px-4 py-2">
              <Hand class="h-3 w-3 text-indigo-400" />
              <span class="text-[9px] font-bold uppercase tracking-widest text-indigo-400">手势或方向键控制</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="knowledgeDetailOpen && selectedKnowledgeContent"
      class="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 px-4 py-6 backdrop-blur-sm sm:items-center"
      data-testid="healing-knowledge-detail"
      role="dialog"
      aria-modal="true"
    >
      <div class="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-[24px] bg-white shadow-2xl dark:bg-slate-950">
        <div class="sticky top-0 z-10 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 p-6 text-white">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <h3 class="mb-2 text-2xl font-bold leading-tight text-white">{{ selectedKnowledgeContent.title }}</h3>
              <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-white/80">
                <span v-if="selectedKnowledgeContent.author" class="inline-flex items-center gap-1">
                  <Award class="h-4 w-4" />
                  {{ selectedKnowledgeContent.author }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Clock3 class="h-4 w-4" />
                  {{ formatTimeAgo(selectedKnowledgeContent.created_at) }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Eye class="h-4 w-4" />
                  {{ selectedKnowledgeContent.view_count || 0 }}
                </span>
              </div>
            </div>
            <button class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white/80 transition hover:bg-white/20 hover:text-white" type="button" @click="closeKnowledgeDetail">
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="max-h-[calc(90vh-144px)] overflow-y-auto px-6 py-4">
          <div class="space-y-6">
            <div v-if="selectedKnowledgeContent.content_type === 'video' && selectedKnowledgeContent.content_url" class="relative aspect-video w-full overflow-hidden rounded-xl bg-black">
              <video
                class="h-full w-full object-contain"
                controls
                playsinline
                preload="metadata"
                :poster="knowledgeThumbnail(selectedKnowledgeContent)"
                :src="selectedKnowledgeContent.content_url"
                @loadedmetadata="knowledgeVideoError = ''"
                @play="knowledgeVideoError = ''"
                @error="knowledgeVideoError = '视频加载失败，请检查网络或稍后重试'"
              />
              <div v-if="knowledgeVideoError" class="absolute inset-x-4 top-4 rounded-lg bg-red-500/90 px-3 py-2 text-sm text-white">
                {{ knowledgeVideoError }}
              </div>
            </div>
            <div v-if="selectedKnowledgeContent.content_type === 'article'" class="flex items-center gap-2">
              <span class="inline-flex items-center gap-2 rounded-full bg-sky-500 px-3 py-1.5 text-xs font-semibold text-white">
                <FileText class="h-3.5 w-3.5" />
                文章
              </span>
            </div>

            <div class="whitespace-pre-wrap text-base leading-relaxed text-slate-800 dark:text-slate-100 md:text-lg">
              {{ selectedKnowledgeArticleText }}
            </div>

            <div class="flex items-center gap-4 border-y border-slate-100 py-4 dark:border-slate-800">
              <button class="inline-flex items-center gap-2 rounded-full px-2 py-2 text-sm font-medium text-slate-500 transition hover:scale-110 hover:text-pink-500 dark:text-slate-400" type="button" @click="likeKnowledgeContent(selectedKnowledgeContent)">
                <ThumbsUp class="h-5 w-5" />
                {{ selectedKnowledgeContent.like_count || 0 }}
              </button>
              <button class="inline-flex items-center gap-2 rounded-full px-2 py-2 text-sm font-medium text-slate-500 transition hover:scale-110 hover:text-blue-500 dark:text-slate-400" type="button">
                <MessageCircle class="h-5 w-5" />
                0
              </button>
              <button
                class="inline-flex items-center gap-2 rounded-full px-2 py-2 text-sm font-medium transition hover:scale-110"
                :class="favoriteContentIds.has(selectedKnowledgeContent.id) ? 'text-amber-500 hover:text-amber-600' : 'text-slate-500 hover:text-amber-500 dark:text-slate-400'"
                type="button"
                @click="toggleKnowledgeFavorite(selectedKnowledgeContent.id)"
              >
                <Bookmark class="h-5 w-5" :class="favoriteContentIds.has(selectedKnowledgeContent.id) ? 'fill-current' : ''" />
                收藏
              </button>
              <button class="ml-auto inline-flex items-center gap-2 rounded-full px-2 py-2 text-sm font-medium text-slate-500 transition hover:scale-110 hover:text-green-500 dark:text-slate-400" type="button" @click="knowledgeShareDialogOpen = true">
                <Share2 class="h-5 w-5" />
                分享
              </button>
            </div>
            <button
              v-if="isInterventionMode"
              class="flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-black transition"
              :class="canCompleteIntervention ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 text-slate-400 dark:bg-slate-800'"
              :disabled="!canCompleteIntervention || interventionCompleting"
              type="button"
              @click="completeKnowledgeIntervention"
            >
              <Check class="h-4 w-4" />
              {{ interventionCompleted ? '今日已完成' : canCompleteIntervention ? '记录知识学习完成' : `${interventionRemaining} 秒后可完成` }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="knowledgeShareDialogOpen && selectedKnowledgeContent"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 px-4 py-6 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-md rounded-[20px] bg-white p-6 shadow-2xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white">
              <Share2 class="h-5 w-5 text-primary" />
              分享到
            </h3>
            <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">选择一种分享方式</p>
          </div>
          <button class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-900" type="button" @click="knowledgeShareDialogOpen = false">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="space-y-3 py-4">
          <button class="flex h-14 w-full items-center rounded-[16px] border border-blue-200 bg-gradient-to-r from-blue-50 to-cyan-50 px-3 text-left text-blue-700 transition hover:scale-[1.02] hover:from-blue-100 hover:to-cyan-100 dark:border-blue-800 dark:from-blue-950/30 dark:to-cyan-950/30 dark:text-blue-300" type="button" @click="copyKnowledgeLink">
            <span class="mr-3 flex h-10 w-10 items-center justify-center rounded-full bg-blue-500">
              <Copy class="h-5 w-5 text-white" />
            </span>
            <span class="flex-1">
              <span class="block font-semibold">复制链接</span>
              <span class="block text-xs opacity-70">将链接分享给好友</span>
            </span>
          </button>
          <button class="flex h-14 w-full items-center rounded-[16px] border border-green-200 bg-gradient-to-r from-green-50 to-emerald-50 px-3 text-left text-green-700 transition hover:scale-[1.02] hover:from-green-100 hover:to-emerald-100 dark:border-green-800 dark:from-green-950/30 dark:to-emerald-950/30 dark:text-green-300" type="button" @click="showToast('请在微信中打开此页面进行分享', 'info'); knowledgeShareDialogOpen = false">
            <span class="mr-3 flex h-10 w-10 items-center justify-center rounded-full bg-green-500">
              <MessageCircle class="h-5 w-5 text-white" />
            </span>
            <span class="flex-1">
              <span class="block font-semibold">微信好友</span>
              <span class="block text-xs opacity-70">分享到微信好友或群</span>
            </span>
          </button>
          <button class="flex h-14 w-full items-center rounded-[16px] border border-purple-200 bg-gradient-to-r from-purple-50 to-pink-50 px-3 text-left text-purple-700 transition hover:scale-[1.02] hover:from-purple-100 hover:to-pink-100 dark:border-purple-800 dark:from-purple-950/30 dark:to-pink-950/30 dark:text-purple-300" type="button" @click="showToast('海报生成功能开发中...', 'info'); knowledgeShareDialogOpen = false">
            <span class="mr-3 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
              <Link2 class="h-5 w-5 text-white" />
            </span>
            <span class="flex-1">
              <span class="block font-semibold">生成海报</span>
              <span class="block text-xs opacity-70">生成精美图片分享</span>
            </span>
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="moodDialogOpen && completedSession"
      class="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 px-4 py-6 backdrop-blur-sm sm:items-center"
      data-testid="healing-mood-dialog"
      role="dialog"
      aria-modal="true"
    >
      <div class="w-full max-w-xl rounded-[28px] bg-white p-5 shadow-2xl dark:bg-slate-950">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-500">Meditation Complete</p>
            <h3 class="mt-2 text-xl font-black text-slate-900 dark:text-white">记录本次冥想感受</h3>
            <p class="mt-2 text-sm text-slate-500">
              {{ completedSession.title }} · {{ formatTime(completedSession.duration) }}
            </p>
          </div>
          <button
            class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-300"
            type="button"
            @click="closeCompletionDialog"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-5">
          <button
            v-for="item in moodOptions"
            :key="item.value"
            class="rounded-[18px] border px-3 py-3 text-sm font-semibold transition"
            :class="
              moodAfter === item.value
                ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200'
                : 'border-slate-100 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300'
            "
            :data-testid="`healing-mood-${item.value}`"
            type="button"
            @click="moodAfter = item.value"
          >
            <span class="block text-xl">{{ item.emoji }}</span>
            <span class="mt-1 block">{{ item.label }}</span>
          </button>
        </div>

        <textarea
          v-model="sessionNotes"
          class="mt-4 min-h-28 w-full rounded-[20px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900"
          data-testid="healing-session-notes"
          placeholder="可以补充一句本次练习后的身体感受。"
        />

        <div class="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            class="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-600 dark:bg-slate-900 dark:text-slate-300"
            type="button"
            @click="closeCompletionDialog"
          >
            稍后再记
          </button>
          <button
            class="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60 dark:bg-white dark:text-slate-900"
            :disabled="savingSession"
            data-testid="healing-confirm-session"
            type="button"
            @click="saveMeditationSession"
          >
            <span class="inline-flex items-center gap-2">
              <Check class="h-4 w-4" />
              {{ savingSession ? '保存中...' : '保存冥想记录' }}
            </span>
          </button>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>
