<script setup lang="ts">
import {
  Activity,
  Camera,
  Clock,
  ChevronRight,
  Copy,
  Crown,
  Edit3,
  FileText,
  HelpCircle,
  ImageIcon,
  LogOut,
  Mail,
  MessageSquare,
  Phone,
  Ruler,
  Scale,
  Settings,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Upload,
  User,
  Watch,
  X,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useAppState } from '@/composables/useAppState'
import { useAuthSession } from '@/composables/useAuthSession'
import { updateProfile } from '@/db/api'
import { publicStorageUrl, uploadStorageFile } from '@/lib/backend-api'
import { PRESET_AVATARS, resolveAvatarSource } from '@/lib/avatar-presets'
import { exportElementReport } from '@/utils/report-export'

const PRESET_BACKGROUNDS = [
  { id: 'bg1', label: '深海蓝', className: 'from-blue-500 via-indigo-500 to-violet-600' },
  { id: 'bg2', label: '森林绿', className: 'from-emerald-400 via-teal-500 to-cyan-600' },
  { id: 'bg3', label: '晚霞粉', className: 'from-rose-400 via-pink-500 to-purple-600' },
] as const

const router = useRouter()
const route = useRoute()
const { state, refreshCurrentAccountProfile, refreshAssessments } = useAppState()
const { state: authState, refreshProfile, signInWithUsername, signOut } = useAuthSession()

const profileForm = reactive({
  fullName: '',
  phone: '',
  gender: 'other',
  age: '',
  height: '',
  weight: '',
  wechat: '',
  email: '',
})

const selectedAvatar = ref('avatar5')
const customAvatarUrl = ref<string | null>(null)
const selectedBackground = ref('bg3')
const customBackgroundUrl = ref<string | null>(null)
const isEditing = ref(false)
const activeEditTab = ref<'profile' | 'avatar' | 'background'>('profile')
const uploadingImage = ref(false)
const savingProfile = ref(false)
const doctorDialogOpen = ref(false)
const doctorUsername = ref('')
const doctorPassword = ref('')
const doctorLoading = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error' | 'warning' | 'info'>('info')
const avatarInput = ref<HTMLInputElement | null>(null)
const backgroundInput = ref<HTMLInputElement | null>(null)
const showFusionReport = computed(() => route.query.openReport === '1')
let toastTimer: number | null = null

const showToast = (message: string, tone: 'success' | 'error' | 'warning' | 'info' = 'info', duration = 1800) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const clearToast = () => {
  toastMessage.value = ''
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
    toastTimer = null
  }
}
const stats = reactive({
  emotionScore: 75,
  consecutiveDays: 0,
  assessmentCount: 0,
  diaryCount: 0,
})

const roleLabel = computed(() => {
  switch ((authState.profile?.role || state.currentAccountRole || '').toLowerCase()) {
    case 'user':
      return '用户端'
    case 'doctor':
      return '管理员端'
    case 'admin':
      return '管理员端'
    case 'super_admin':
      return '超级管理员'
    default:
      return '未登录'
  }
})

const menuItems = computed(() => [
  { label: '手环数据', path: '/profile/smart-band', value: '智能健康监测', icon: Watch, accent: 'text-violet-600', surface: 'bg-violet-50' },
  { label: '疗愈计划', path: '/profile/healing-plan', value: '专属定制方案', icon: Sparkles, accent: 'text-indigo-600', surface: 'bg-indigo-50' },
  { label: '对接管理员', path: '/profile/connect-doctor', value: '专业专家问诊', icon: Stethoscope, accent: 'text-rose-600', surface: 'bg-rose-50' },
  { label: '会员订阅', path: '/profile/subscription', value: '开通享特权', icon: Crown, accent: 'text-amber-600', surface: 'bg-amber-50' },
  { label: '隐私安全', path: '/profile/privacy', value: '账号安全加固', icon: ShieldCheck, accent: 'text-emerald-600', surface: 'bg-emerald-50' },
  { label: '关于我们', path: '/profile/about', value: '版本v1.0', icon: HelpCircle, accent: 'text-slate-600', surface: 'bg-slate-50' },
  {
    label: roleLabel.value === '超级管理员' ? '超级管理员端' : roleLabel.value === '管理员端' ? '管理员后台' : '管理员后台登录',
    path: '/admin/dashboard',
    value: '',
    icon: Settings,
    accent: 'text-slate-600',
    surface: 'bg-slate-50',
  },
])

const latestFusionReport = computed(() => state.assessments[0] || null)

const fusionRiskLevel = computed(() => {
  const score = latestFusionReport.value?.overall.score ?? 0
  if (score >= 75) return { label: '高风险', tone: 'text-rose-600 bg-rose-50 border-rose-100', alert: true }
  if (score >= 55) return { label: '中风险', tone: 'text-amber-600 bg-amber-50 border-amber-100', alert: false }
  return { label: '低风险', tone: 'text-emerald-600 bg-emerald-50 border-emerald-100', alert: false }
})

const fusionSummary = computed(() => {
  if (!latestFusionReport.value) {
    return '当前还没有可展示的融合报告。完成一次多模态评估后，系统会在这里汇总量表、语音与表情结果。'
  }
  return latestFusionReport.value.overall.summary
})

const reportSections = computed(() => {
  const report = latestFusionReport.value
  if (!report) return []
  return [
    { title: '1. 心理量表评估', action: '下载量表报告', item: report.scale },
    { title: '2. 语音情绪识别', action: '下载语音报告', item: report.voice },
    { title: '3. 表情微反应分析', action: '下载表情报告', item: report.expression },
  ]
})

const fusionWeights = { scale: 0.5, voice: 0.2, expression: 0.3 }
const activeReport = ref<'scale' | 'voice' | 'expression' | null>(null)
const reportLoading = ref(false)
const reportSyncStatus = ref<'idle' | 'syncing' | 'success' | 'error'>('success')
const reportHistoryOpen = ref(false)
const reportHistoryLoading = ref(false)
const selectedHistoryId = ref<string | null>(null)
const profileFusionReportEl = ref<HTMLElement | null>(null)
const reportLoadedFromBackend = ref(false)

const selectedProfileReport = computed(() => {
  const selected = selectedHistoryId.value
    ? state.assessments.find((item) => item.id === selectedHistoryId.value)
    : null
  return selected || latestFusionReport.value
})

const fusionReportData = computed(() => {
  const raw = selectedProfileReport.value?.report || {}
  const fusionAi = raw.fusionAi || raw.fusion_ai || {}
  const fusionRecommendations = Array.isArray(fusionAi.recommendations)
    ? fusionAi.recommendations.map((item: unknown, index: number) => `${index + 1}. ${String(item)}`).join('\n')
    : ''
  return {
    scaleData: raw.scaleData || raw.scale || null,
    voiceData: raw.voiceData || raw.voice || null,
    expressionData: raw.expressionData || raw.expression || null,
    advice: String(
      raw.advice ||
        raw.overall?.advice ||
        fusionRecommendations ||
        fusionAi.detailedReport ||
        fusionAi.detailed_report ||
        selectedProfileReport.value?.overall?.summary ||
        raw.overall?.summary ||
        '',
    ).trim(),
  }
})

const getScaleScore = (value: any) => Number(value?.score ?? value?.phq9_score ?? 0)
const getVoiceScore = (value: any) => Number(value?.score ?? value?.risk_score ?? value?.emotion_score ?? 0)
const getExpressionScore = (value: any) => Number(value?.depression_risk_score ?? value?.risk_score ?? 0)

const hasScaleReport = computed(() => Boolean(fusionReportData.value.scaleData && getScaleScore(fusionReportData.value.scaleData) > 0))
const hasVoiceReport = computed(() => Boolean(
  fusionReportData.value.voiceData &&
    (fusionReportData.value.voiceData.text || fusionReportData.value.voiceData.speech_metrics || fusionReportData.value.voiceData.emotion_vector || fusionReportData.value.voiceData.emotions),
))
const hasExpressionReport = computed(() => Boolean(
  fusionReportData.value.expressionData &&
    (fusionReportData.value.expressionData.emotion_radar || fusionReportData.value.expressionData.facial_expressions) &&
    (fusionReportData.value.expressionData.analysis_report || fusionReportData.value.expressionData.micro_features),
))

const hasCompleteProfileFusionReport = computed(() =>
  Boolean(selectedProfileReport.value && hasScaleReport.value && hasVoiceReport.value && hasExpressionReport.value),
)

const calculateScaleNormalized = (scaleRaw: number) => {
  if (scaleRaw <= 4) return scaleRaw * 5
  if (scaleRaw <= 9) return 20 + (scaleRaw - 5) * 4
  if (scaleRaw <= 14) return 40 + (scaleRaw - 10) * 4
  if (scaleRaw <= 19) return 60 + (scaleRaw - 15) * 4
  return 80 + (scaleRaw - 20) * 2.5
}

const profileFusionScore = computed(() => {
  const savedScore = Number(selectedProfileReport.value?.overall?.score ?? selectedProfileReport.value?.report?.overall?.score)
  if (Number.isFinite(savedScore) && savedScore > 0) {
    return Math.round(savedScore)
  }
  const data = fusionReportData.value
  return Math.round(
    calculateScaleNormalized(getScaleScore(data.scaleData)) * fusionWeights.scale +
      getVoiceScore(data.voiceData) * fusionWeights.voice +
      getExpressionScore(data.expressionData) * fusionWeights.expression,
  )
})

const profileRiskLevel = computed<'low' | 'medium' | 'high' | 'extreme'>(() => {
  const score = profileFusionScore.value
  if (score >= 80) return 'extreme'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
})

const profileRiskText = computed(() => {
  if (profileRiskLevel.value === 'extreme') return '极高风险'
  if (profileRiskLevel.value === 'high') return '高风险'
  if (profileRiskLevel.value === 'medium') return '中风险'
  return '低风险'
})

const profileRiskClass = computed(() => {
  if (profileRiskLevel.value === 'extreme') return 'bg-rose-600 shadow-rose-600/20'
  if (profileRiskLevel.value === 'high') return 'bg-orange-500 shadow-orange-500/20'
  if (profileRiskLevel.value === 'medium') return 'bg-violet-500 shadow-violet-500/20'
  return 'bg-emerald-500 shadow-emerald-500/20'
})

const scaleDimensionScores = computed(() => {
  const scores = fusionReportData.value.scaleData?.dimensionScores || fusionReportData.value.scaleData?.dimension_scores
  return Array.isArray(scores) && scores.length > 0 ? scores : []
})

const voiceEmotionItems = computed(() => {
  const emotions = fusionReportData.value.voiceData?.emotions || fusionReportData.value.voiceData?.emotion_vector || {}
  return [
    { label: '平静', value: Number(emotions.calm ?? 0) },
    { label: '开心', value: Number(emotions.happy ?? 0) },
    { label: '悲伤', value: Number(emotions.sad ?? 0) },
    { label: '愤怒', value: Number(emotions.angry ?? 0) },
    { label: '恐惧', value: Number(emotions.fear ?? emotions.fearful ?? 0) },
    { label: '惊讶', value: Number(emotions.surprise ?? emotions.surprised ?? 0) },
  ]
})

const expressionRadarItems = computed(() => {
  const facial = fusionReportData.value.expressionData?.facial_expressions || fusionReportData.value.expressionData?.emotion_radar || {}
  return [
    { key: 'neutral', label: '中性', value: Number(facial.neutral ?? 0) },
    { key: 'happy', label: '高兴', value: Number(facial.happy ?? 0) },
    { key: 'sad', label: '悲伤', value: Number(facial.sad ?? 0) },
    { key: 'angry', label: '愤怒', value: Number(facial.angry ?? 0) },
    { key: 'surprised', label: '惊讶', value: Number(facial.surprised ?? 0) },
    { key: 'fearful', label: '恐惧', value: Number(facial.fearful ?? 0) },
    { key: 'disgusted', label: '厌恶', value: Number(facial.disgusted ?? 0) },
    { key: 'contempt', label: '轻蔑', value: Number(facial.contempt ?? 0) },
    { key: 'pain', label: '痛苦', value: Number(facial.pain ?? 0) },
  ]
})

const professionalAdvice = computed(() => {
  const saved = fusionReportData.value.advice
  if (saved) return saved
  if (!hasScaleReport.value || !hasVoiceReport.value || !hasExpressionReport.value) {
    return '当前报告尚未包含完整的量表、语音或表情结果。请完成一次多模态评估后，再查看综合诊断结论。'
  }
  return '该报告缺少 AI 融合诊断结论，请重新完成多模态评估后生成完整报告。'
})

const exportProfileFusionReport = async (format: 'pdf' | 'png') => {
  try {
    await exportElementReport(profileFusionReportEl.value, format, 'FusionReport')
    showToast('下载成功', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '下载失败', 'error')
  }
}

const openReportWithDelay = async () => {
  if (reportLoading.value) return
  reportLoading.value = true
  try {
    window.setTimeout(() => {
      router.push('/profile?openReport=1')
      reportLoading.value = false
      void refreshAssessments().then(() => {
        reportLoadedFromBackend.value = true
      })
    }, 3000)
  } catch (error) {
    showToast(error instanceof Error ? `健康报告加载失败：${error.message}` : '健康报告加载失败', 'error')
    reportLoading.value = false
  }
}

const openReportHistory = async () => {
  reportHistoryOpen.value = true
  reportHistoryLoading.value = true
  clearToast()
  try {
    await refreshAssessments()
    reportLoadedFromBackend.value = true
  } catch (error) {
    showToast(error instanceof Error ? `历史记录加载失败：${error.message}` : '历史记录加载失败', 'error')
  } finally {
    reportHistoryLoading.value = false
  }
}

const currentAvatarPreset = computed(() => PRESET_AVATARS.find((item) => item.id === selectedAvatar.value) || PRESET_AVATARS[4])
const currentBackgroundPreset = computed(
  () => PRESET_BACKGROUNDS.find((item) => item.id === selectedBackground.value) || PRESET_BACKGROUNDS[2],
)

const headerStyle = computed(() => {
  if (customBackgroundUrl.value) {
    return {
      backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.35), rgba(15, 23, 42, 0.35)), url(${customBackgroundUrl.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  return {}
})

const avatarImageUrl = computed(() => customAvatarUrl.value)

const birthDateFromAge = (age: string) => {
  const numericAge = Number(age)
  if (!age || Number.isNaN(numericAge) || numericAge <= 0) return null
  return `${new Date().getFullYear() - numericAge}-01-01`
}

const loadFormFromProfile = () => {
  const profile = authState.profile
  if (!profile) return

  profileForm.fullName = profile.full_name || ''
  profileForm.phone = profile.phone || ''
  profileForm.gender = profile.gender || 'other'
  profileForm.wechat = profile.wechat || ''
  profileForm.email = profile.email || ''

  if (profile.birth_date) {
    const today = new Date()
    const birth = new Date(profile.birth_date)
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age -= 1
    }
    profileForm.age = String(age)
  } else {
    profileForm.age = ''
  }

  profileForm.height = ''
  profileForm.weight = ''
  if (profile.bio) {
    try {
      const bio = JSON.parse(profile.bio)
      profileForm.height = bio.height ? String(bio.height) : ''
      profileForm.weight = bio.weight ? String(bio.weight) : ''
    } catch {
      profileForm.height = ''
      profileForm.weight = ''
    }
  }

  const avatarSource = resolveAvatarSource(profile.avatar_url)
  selectedAvatar.value = avatarSource.preset?.id || 'avatar5'
  customAvatarUrl.value = avatarSource.imageUrl

  if (profile.background_url?.startsWith('preset:')) {
    selectedBackground.value = profile.background_url.slice('preset:'.length)
    customBackgroundUrl.value = null
  } else if (profile.background_url) {
    customBackgroundUrl.value = profile.background_url
  } else {
    selectedBackground.value = profile.selected_background || 'bg3'
    customBackgroundUrl.value = null
  }
}

const uploadImage = async (file: File, folder: 'avatars' | 'backgrounds') => {
  if (!authState.user) throw new Error('当前未登录')
  const ext = file.name.split('.').pop() || 'jpg'
  const path = `${folder}/${authState.user.id}_${Date.now()}.${ext}`
  const uploaded = await uploadStorageFile('diary-images', path, file)
  return uploaded.publicUrl || publicStorageUrl('diary-images', uploaded.path)
}

const fileToDataUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('图片读取失败'))
    reader.readAsDataURL(file)
  })

const onImageSelected = async (event: Event, target: 'avatar' | 'background') => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    showToast('图片大小不能超过 5MB', 'error')
    input.value = ''
    return
  }

  uploadingImage.value = true
  clearToast()
  try {
    const url = await uploadImage(file, target === 'avatar' ? 'avatars' : 'backgrounds')
    if (target === 'avatar') {
      customAvatarUrl.value = url
    } else {
      customBackgroundUrl.value = url
    }
    showToast(target === 'avatar' ? '头像已上传' : '背景已上传', 'success')
  } catch {
    try {
      const dataUrl = await fileToDataUrl(file)
      if (target === 'avatar') {
        customAvatarUrl.value = dataUrl
      } else {
        customBackgroundUrl.value = dataUrl
      }
      showToast(target === 'avatar' ? '头像已加载（将在保存时上传）' : '背景已加载（将在保存时上传）', 'warning')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '上传失败', 'error')
    }
  } finally {
    uploadingImage.value = false
    input.value = ''
  }
}

const saveProfile = async () => {
  if (!authState.user || !authState.profile) return

  savingProfile.value = true
  clearToast()
  try {
    const bio: Record<string, number> = {}
    if (profileForm.height) bio.height = Number(profileForm.height)
    if (profileForm.weight) bio.weight = Number(profileForm.weight)

    await updateProfile(authState.user.id, {
      full_name: profileForm.fullName || null,
      phone: profileForm.phone || null,
      gender: profileForm.gender || 'other',
      role: authState.profile.role,
      avatar_url: customAvatarUrl.value || `preset:${selectedAvatar.value}`,
      background_url: customBackgroundUrl.value || `preset:${selectedBackground.value}`,
      selected_background: selectedBackground.value,
      birth_date: birthDateFromAge(profileForm.age),
      wechat: profileForm.wechat || null,
      email: profileForm.email || null,
      bio: Object.keys(bio).length > 0 ? JSON.stringify(bio) : null,
    })

    await Promise.all([refreshProfile(), refreshCurrentAccountProfile()])
    loadFormFromProfile()
    isEditing.value = false
    showToast('保存成功', 'success')
  } catch (error) {
    showToast(error instanceof Error ? `保存失败：${error.message}` : '保存失败：请重试', 'error')
  } finally {
    savingProfile.value = false
  }
}

const copyUserId = async () => {
  if (!authState.user?.id) return
  try {
    await navigator.clipboard.writeText(authState.user.id)
    showToast('ID已复制到剪贴板', 'success')
  } catch {
    showToast('复制失败', 'error')
  }
}

const handleLogout = async () => {
  await signOut()
  router.push('/login')
}

const openMenuItem = (item: { label: string; path: string }) => {
  if (item.path !== '/admin/dashboard') {
    router.push(item.path)
    return
  }
  if (roleLabel.value === '超级管理员') {
    router.push('/admin/dashboard')
    return
  }
  if (roleLabel.value === '管理员端') {
    router.push('/admin/dashboard')
    return
  }
  doctorDialogOpen.value = true
}

const handleDoctorLogin = async () => {
  if (!doctorUsername.value || !doctorPassword.value) {
    showToast('请输入用户名和密码', 'error')
    return
  }
  doctorLoading.value = true
  clearToast()
  try {
    const { error } = await signInWithUsername(doctorUsername.value, doctorPassword.value)
    if (error) {
      showToast(`登录失败: ${error.message}`, 'error')
      return
    }
    await Promise.all([refreshProfile(), refreshCurrentAccountProfile()])
    if (authState.profile?.role === 'super_admin') {
      doctorDialogOpen.value = false
      showToast('登录成功，正在进入管理员后台', 'success')
      router.push('/admin/dashboard')
    } else if (authState.profile?.role === 'doctor' || authState.profile?.role === 'admin') {
      doctorDialogOpen.value = false
      showToast('登录成功，正在进入管理员后台', 'success')
      router.push('/admin/dashboard')
    } else {
      showToast('当前账户非管理员角色，无法进入管理员后台', 'error')
    }
  } finally {
    doctorLoading.value = false
  }
}

watch(
  () => authState.profile,
  () => {
    loadFormFromProfile()
  },
  { immediate: true },
)

onMounted(async () => {
  await refreshCurrentAccountProfile().catch(() => undefined)
  if (route.query.openReport === '1') {
    try {
      reportLoading.value = true
      await refreshAssessments()
      reportLoadedFromBackend.value = true
    } catch (error) {
      showToast(error instanceof Error ? `健康报告加载失败：${error.message}` : '健康报告加载失败', 'error')
    } finally {
      reportLoading.value = false
    }
  }
  loadFormFromProfile()
})

onBeforeUnmount(() => {
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="bg-background pb-12">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : toastTone === 'success' ? 'bg-emerald-600 shadow-emerald-900/20' : toastTone === 'warning' ? 'bg-amber-600 shadow-amber-900/20' : 'bg-slate-950 shadow-slate-900/20'"
      data-testid="profile-toast"
    >
      {{ toastMessage }}
    </div>
    <div
      class="overflow-hidden px-5 pb-16 pt-8 text-white md:px-8 md:pb-20 md:pt-12"
      :class="customBackgroundUrl ? 'bg-slate-900' : `bg-gradient-to-br ${currentBackgroundPreset.className}`"
      :style="headerStyle"
    >
      <div class="page-grid relative">
        <div class="absolute -right-12 -top-12 h-44 w-44 rounded-full bg-white/10 blur-3xl" />
        <div class="absolute -bottom-10 -left-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />

        <div class="relative flex items-start gap-4 md:gap-6">
          <div class="relative shrink-0">
            <div class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full border-[3px] border-white/80 bg-white shadow-xl md:h-20 md:w-20">
              <img v-if="avatarImageUrl" :src="avatarImageUrl" alt="头像" class="h-full w-full object-cover" />
              <div
                v-else
                :class="['flex h-full w-full items-center justify-center text-2xl md:text-3xl', currentAvatarPreset.bg]"
              >
                {{ currentAvatarPreset.emoji }}
              </div>
            </div>
            <div class="absolute -bottom-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-emerald-500 md:h-6 md:w-6">
              <div class="h-1.5 w-1.5 rounded-full bg-white md:h-2 md:w-2" />
            </div>
          </div>

          <div class="min-w-0 flex-1 pt-1">
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="truncate text-xl font-bold md:text-2xl">
                {{ authState.profile?.username || state.profile.username || '心域用户' }}
              </h1>
              <span class="rounded-full bg-emerald-500 px-3 py-1 text-xs font-semibold text-white">
                已认证
              </span>
            </div>
            <div class="mt-3 flex flex-wrap items-center gap-3">
              <button
                class="inline-flex items-center gap-2 rounded bg-white/20 px-2 py-0.5 text-[10px] font-semibold text-white/90 transition hover:bg-white/30"
                type="button"
                @click="copyUserId"
              >
                <span class="font-bold uppercase tracking-wider text-white/80">ID</span>
                {{ authState.user?.id ? `${authState.user.id.slice(0, 4)}****${authState.user.id.slice(-4)}` : '未登录' }}
                <span class="text-white/60">复制</span>
              </button>
            </div>
          </div>

          <button
            class="mt-6 mr-2 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-white/90 backdrop-blur-sm transition hover:bg-white/20 hover:text-white"
            type="button"
            aria-label="编辑资料"
            data-testid="profile-edit-trigger"
            @click="isEditing = true"
          >
            <Edit3 class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <div class="page-grid relative z-10 -mt-10 space-y-4 pb-10">
      <BaseCard class="border-white/60 bg-white/75 backdrop-blur-xl dark:bg-slate-900/75">
        <div class="relative overflow-hidden rounded-[8px]">
          <div v-if="reportLoading" class="absolute inset-x-0 bottom-0 h-1 bg-slate-200/50">
            <div class="h-full animate-[profile-report-loading_3s_ease-in-out_forwards] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
          </div>
        </div>
        <button class="flex w-full items-center justify-between gap-4 text-left" data-testid="profile-health-report-card" type="button" @click="openReportWithDelay">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-[8px] bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
              <span v-if="reportLoading" class="h-6 w-6 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              <FileText v-else class="h-6 w-6" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">{{ reportLoading ? '生成报告中...' : '查看健康报告' }}</h2>
              <p class="mt-1 text-sm text-slate-500">{{ reportLoading ? 'AI正在分析您的健康数据' : '多模态评估结果与康复建议' }}</p>
            </div>
          </div>
        </button>
      </BaseCard>

      <BaseCard class="border-0 shadow-sm">
        <div class="overflow-hidden rounded-[8px] bg-white dark:bg-slate-950">
          <button
            v-for="item in menuItems"
            :key="item.path"
            class="flex w-full items-center gap-4 border-b border-slate-100 px-1 py-4 text-left last:border-b-0 dark:border-slate-800"
            type="button"
            @click="openMenuItem(item)"
          >
            <div :class="['flex h-11 w-11 items-center justify-center rounded-[8px]', item.surface, 'dark:bg-slate-800']">
              <component :is="item.icon" :class="['h-5 w-5', item.accent, 'dark:text-slate-200']" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-semibold text-slate-900 dark:text-white">{{ item.label }}</p>
              <p class="mt-1 text-xs text-slate-400">{{ item.value }}</p>
            </div>
            <ChevronRight class="h-4 w-4 text-slate-300" />
          </button>
        </div>
      </BaseCard>

      <button
        class="flex h-14 w-full items-center justify-center gap-2 rounded-[32px] text-sm font-bold text-rose-500 transition hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30 md:h-16 md:text-base"
        type="button"
        @click="handleLogout"
      >
        <LogOut class="h-5 w-5 md:h-6 md:w-6" />
        退出当前账号
      </button>

      <div class="space-y-1 py-4 text-center">
        <p class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-300 dark:text-slate-700">
          初心 V1.0.0
        </p>
        <p class="text-[9px] text-slate-200 dark:text-slate-800">
          © 2026 初心团队
        </p>
      </div>
    </div>

    <div v-if="isEditing" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="profile-edit-dialog">
      <section class="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl dark:bg-slate-950">
        <header class="flex items-start justify-between gap-4 border-b border-slate-100 p-5 dark:border-slate-800">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 text-white">
              <User class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-xl font-bold text-slate-900 dark:text-white">编辑个人资料</h2>
              <p class="mt-1 text-sm text-slate-500">自定义您的头像、背景和基本信息</p>
            </div>
          </div>
          <button class="grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900" type="button" @click="isEditing = false">
            <X class="h-5 w-5" />
          </button>
        </header>

        <div class="overflow-y-auto p-5">
          <div class="grid rounded-xl bg-slate-100 p-1 text-xs font-bold text-slate-500 dark:bg-slate-900 dark:text-slate-400 sm:grid-cols-3">
            <button
              class="inline-flex h-10 items-center justify-center gap-2 rounded-lg transition"
              :class="activeEditTab === 'profile' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white' : ''"
              type="button"
              @click="activeEditTab = 'profile'"
            >
              <User class="h-3.5 w-3.5" />
              基本信息
            </button>
            <button
              class="inline-flex h-10 items-center justify-center gap-2 rounded-lg transition"
              :class="activeEditTab === 'avatar' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white' : ''"
              type="button"
              @click="activeEditTab = 'avatar'"
            >
              <Camera class="h-3.5 w-3.5" />
              头像设置
            </button>
            <button
              class="inline-flex h-10 items-center justify-center gap-2 rounded-lg transition"
              :class="activeEditTab === 'background' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white' : ''"
              type="button"
              @click="activeEditTab = 'background'"
            >
              <ImageIcon class="h-3.5 w-3.5" />
              背景主题
            </button>
          </div>

          <div v-if="activeEditTab === 'profile'" class="mt-5 space-y-5">
            <section class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="flex h-6 w-6 items-center justify-center rounded-md bg-blue-100 text-blue-600">
                  <User class="h-3.5 w-3.5" />
                </div>
                <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">身份信息</span>
              </div>
              <div class="space-y-1.5">
                <label class="text-sm font-medium text-slate-700 dark:text-slate-200">真实姓名</label>
                <input v-model="profileForm.fullName" data-testid="profile-full-name-input" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="请输入您的姓名" />
              </div>
              <div class="space-y-1.5">
                <label class="text-sm font-medium text-slate-700 dark:text-slate-200">性别</label>
                <div class="flex gap-4">
                  <label class="inline-flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
                    <input v-model="profileForm.gender" type="radio" value="male" />
                    男
                  </label>
                  <label class="inline-flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
                    <input v-model="profileForm.gender" type="radio" value="female" />
                    女
                  </label>
                </div>
              </div>
              <div class="space-y-1.5">
                <label class="text-sm font-medium text-slate-700 dark:text-slate-200">年龄</label>
                <input v-model="profileForm.age" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" max="120" min="1" placeholder="请输入年龄" type="number" />
              </div>
            </section>

            <section class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-100 text-emerald-600">
                  <Scale class="h-3.5 w-3.5" />
                </div>
                <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">身体数据</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1.5">
                  <label class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200"><Ruler class="h-3.5 w-3.5" />身高 (cm)</label>
                  <input v-model="profileForm.height" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="175" type="number" />
                </div>
                <div class="space-y-1.5">
                  <label class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200"><Scale class="h-3.5 w-3.5" />体重 (kg)</label>
                  <input v-model="profileForm.weight" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="65" type="number" />
                </div>
              </div>
            </section>

            <section class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="flex h-6 w-6 items-center justify-center rounded-md bg-purple-100 text-purple-600">
                  <Phone class="h-3.5 w-3.5" />
                </div>
                <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">联系方式</span>
              </div>
              <div class="space-y-1.5">
                <label class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200"><Phone class="h-3.5 w-3.5" />手机号</label>
                <input v-model="profileForm.phone" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="请输入手机号" type="tel" />
              </div>
              <div class="space-y-1.5">
                <label class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200"><MessageSquare class="h-3.5 w-3.5" />微信号</label>
                <input v-model="profileForm.wechat" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="请输入微信号" />
              </div>
              <div class="space-y-1.5">
                <label class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200"><Mail class="h-3.5 w-3.5" />邮箱</label>
                <input v-model="profileForm.email" class="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white" placeholder="请输入邮箱" type="email" />
              </div>
            </section>
          </div>

          <div v-else-if="activeEditTab === 'avatar'" class="mt-5 space-y-5">
            <div class="py-4 text-center">
              <div class="relative inline-block">
                <div class="mx-auto flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-4 border-white bg-slate-100 text-5xl shadow-xl">
                  <img v-if="avatarImageUrl" :src="avatarImageUrl" alt="头像" class="h-full w-full object-cover" />
                  <span v-else :class="['flex h-full w-full items-center justify-center', currentAvatarPreset.bg]">{{ currentAvatarPreset.emoji }}</span>
                </div>
                <button class="absolute -bottom-1 -right-1 flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg" type="button" @click="avatarInput?.click()">
                  <Upload class="h-4 w-4" />
                </button>
              </div>
              <p class="mt-3 text-sm text-slate-500">点击上传自定义头像</p>
              <input ref="avatarInput" class="hidden" type="file" accept="image/*" @change="(event) => onImageSelected(event, 'avatar')" />
            </div>
            <div class="space-y-3">
              <p class="text-sm font-medium text-slate-700 dark:text-slate-200">选择预设头像</p>
              <div class="grid grid-cols-5 gap-3">
                <button
                  v-for="avatar in PRESET_AVATARS"
                  :key="avatar.id"
                  :class="[
                    'relative flex aspect-square items-center justify-center rounded-2xl text-3xl shadow-md transition hover:scale-105',
                    selectedAvatar === avatar.id && !customAvatarUrl ? 'ring-2 ring-blue-500 ring-offset-2' : '',
                    avatar.bg,
                  ]"
                  type="button"
                  @click="selectedAvatar = avatar.id; customAvatarUrl = null"
                >
                  {{ avatar.emoji }}
                </button>
              </div>
            </div>
          </div>

          <div v-else class="mt-5 space-y-5">
            <section class="space-y-3">
              <p class="text-sm font-medium text-slate-700 dark:text-slate-200">上传自定义背景</p>
              <button class="flex h-24 w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-slate-300 text-slate-500 transition hover:border-blue-400 hover:bg-blue-50/50 dark:border-slate-700 dark:hover:bg-slate-900" type="button" @click="backgroundInput?.click()">
                <Upload class="h-6 w-6 text-slate-400" />
                <span class="text-xs">点击上传背景图片</span>
              </button>
              <input ref="backgroundInput" class="hidden" type="file" accept="image/*" @change="(event) => onImageSelected(event, 'background')" />
            </section>

            <section class="space-y-3">
              <p class="text-sm font-medium text-slate-700 dark:text-slate-200">选择预设主题</p>
              <div class="grid gap-3">
                <button
                  v-for="background in PRESET_BACKGROUNDS"
                  :key="background.id"
                  :class="[
                    'relative flex h-16 items-center overflow-hidden rounded-xl bg-gradient-to-r px-4 text-left text-sm font-bold text-white shadow-md transition hover:translate-x-1',
                    background.className,
                    selectedBackground === background.id && !customBackgroundUrl ? 'ring-2 ring-blue-500 ring-offset-2' : '',
                  ]"
                  type="button"
                  @click="selectedBackground = background.id; customBackgroundUrl = null"
                >
                  {{ background.label }}
                </button>
              </div>
            </section>
          </div>
        </div>

        <footer class="grid grid-cols-2 gap-3 border-t border-slate-100 p-5 dark:border-slate-800">
          <button class="h-11 rounded-xl border border-slate-200 text-sm font-bold text-slate-700 disabled:opacity-60 dark:border-slate-700 dark:text-slate-200" type="button" :disabled="savingProfile || uploadingImage" @click="isEditing = false">
            取消
          </button>
          <button
            data-testid="profile-save-button"
            class="h-11 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 text-sm font-bold text-white shadow-lg shadow-blue-500/25 disabled:opacity-60"
            :disabled="savingProfile || uploadingImage"
            type="button"
            @click="saveProfile"
          >
            {{ savingProfile ? '保存中...' : '保存更改' }}
          </button>
        </footer>
      </section>
    </div>

    <div v-if="doctorDialogOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" data-testid="profile-doctor-login-dialog">
      <section class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl dark:bg-slate-950">
        <div class="flex items-center justify-between">
          <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
            <Settings class="h-5 w-5 text-emerald-600" />
            管理员后台登录
          </h2>
          <button class="grid h-9 w-9 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" type="button" @click="doctorDialogOpen = false">
            <X class="h-5 w-5 text-slate-400" />
          </button>
        </div>
        <div class="mt-5 space-y-4">
          <div>
            <label class="mb-2 block text-sm text-slate-500" for="doctor-username">用户名</label>
            <input id="doctor-username" v-model="doctorUsername" class="w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900" :disabled="doctorLoading" placeholder="请输入管理员账号用户名" />
          </div>
          <div>
            <label class="mb-2 block text-sm text-slate-500" for="doctor-password">密码</label>
            <input id="doctor-password" v-model="doctorPassword" class="w-full rounded-[8px] border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900" :disabled="doctorLoading" placeholder="请输入密码" type="password" />
          </div>
          <p class="text-xs text-slate-500">登录成功后将进入管理员后台。如非管理员账号，将提示失败。</p>
        </div>
        <div class="mt-5 grid grid-cols-2 gap-3">
          <button class="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" type="button" :disabled="doctorLoading" @click="doctorDialogOpen = false">
            取消
          </button>
          <button class="rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-60" type="button" :disabled="doctorLoading" @click="handleDoctorLogin">
            {{ doctorLoading ? '登录中...' : '登录' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="showFusionReport" class="fixed inset-0 z-50 overflow-y-auto bg-background" data-testid="profile-fusion-report">
      <div class="sticky top-0 z-40 border-b border-slate-100 bg-white px-4 py-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div class="mx-auto flex max-w-md items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <button
              class="-ml-2 inline-flex h-10 w-10 items-center justify-center rounded-full text-slate-900 hover:bg-slate-100 dark:text-white dark:hover:bg-slate-800"
              aria-label="关闭报告"
              data-testid="profile-fusion-close"
              @click="router.replace('/profile')"
            >
              <X class="h-6 w-6" />
            </button>
            <h1 class="text-xl font-bold leading-tight text-slate-900 dark:text-white">多模态报告</h1>
          </div>
          <div class="flex items-center gap-2">
            <button class="inline-flex h-9 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200" data-testid="profile-fusion-history" @click="openReportHistory">
              <Clock class="h-4 w-4" />
              历史记录
            </button>
            <button class="service-button disabled:cursor-not-allowed" data-testid="profile-fusion-export-pdf" :disabled="!hasCompleteProfileFusionReport" @click="exportProfileFusionReport('pdf')">
              <FileText class="h-4 w-4" />
              导出PDF
            </button>
          </div>
        </div>
      </div>

      <div class="mx-auto mt-4 max-w-md px-4">
        <p class="text-sm text-slate-500">基于量表、语音与表情三项结果生成综合分析</p>
      </div>

      <div class="mx-auto max-w-md px-4 py-6">

        <section v-if="!hasCompleteProfileFusionReport" class="rounded-2xl bg-white p-8 text-center shadow-xl shadow-slate-200/60 dark:bg-slate-900 dark:shadow-none" data-testid="profile-fusion-empty">
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800">
            <Activity class="h-8 w-8" />
          </div>
          <h2 class="mt-5 text-xl font-black text-slate-900 dark:text-white">暂无完整多模态报告</h2>
          <p class="mt-3 text-sm leading-7 text-slate-500 dark:text-slate-300">
            完成量表、语音和表情三项评估后，这里会展示同一份融合报告。当前数据不足，暂不生成风险结论。
          </p>
          <button class="mt-6 rounded-full bg-primary px-5 py-3 text-sm font-bold text-white" type="button" @click="router.push('/assessment')">
            去完成评估
          </button>
        </section>

        <section v-else ref="profileFusionReportEl" class="overflow-hidden rounded-2xl bg-white shadow-xl shadow-slate-200/60 dark:bg-slate-900 dark:shadow-none">
          <div class="h-2" :class="profileRiskClass" />
          <div class="p-5 md:p-6">
            <div class="grid grid-cols-3 gap-2">
              <button class="h-10 rounded-[10px] bg-gradient-to-r from-blue-500 to-blue-600 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-blue-500/20" data-testid="profile-fusion-open-scale" @click="activeReport = 'scale'">量表评估报告</button>
              <button class="h-10 rounded-[10px] bg-gradient-to-r from-violet-500 to-purple-600 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-violet-500/20" data-testid="profile-fusion-open-voice" @click="activeReport = 'voice'">语音情绪报告</button>
              <button class="h-10 rounded-[10px] bg-gradient-to-r from-cyan-500 to-teal-500 px-2 text-xs font-bold leading-tight text-white shadow-md shadow-cyan-500/20" data-testid="profile-fusion-open-expression" @click="activeReport = 'expression'">表情识别报告</button>
            </div>

            <div class="mt-6 grid gap-3 md:grid-cols-3">
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">综合风险分</p>
                <p class="mt-2 text-4xl font-black" :class="profileRiskLevel === 'high' || profileRiskLevel === 'extreme' ? 'text-rose-500' : 'text-emerald-500'" data-testid="profile-fusion-score">{{ profileFusionScore }}</p>
                <p class="mt-1 text-[10px] text-slate-400">满分 100</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">风险等级</p>
                <span class="mt-3 inline-flex rounded-full px-3 py-1 text-xs font-bold text-white shadow-lg" :class="profileRiskClass" data-testid="profile-fusion-risk">{{ profileRiskText }}</span>
              </div>
              <div class="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-4 text-center shadow-sm dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
                <p class="text-xs font-medium text-slate-500">同步状态</p>
                <p class="mt-3 text-base font-bold text-slate-800 dark:text-white">{{ reportSyncStatus === 'success' ? '已同步至云端' : '读取报告' }}</p>
                <p class="mt-1 text-[10px] text-slate-400">{{ selectedProfileReport?.createdAt || '暂无报告' }}</p>
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
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><FileText class="h-4 w-4 text-blue-600" />量表评估 (50%)</span>
                    <span class="font-bold">{{ getScaleScore(fusionReportData.scaleData) }} <span class="text-xs text-slate-400">/ 27</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-blue-500" :style="{ width: `${Math.min(100, (getScaleScore(fusionReportData.scaleData) / 27) * 100)}%` }" /></div>
                </div>
                <div>
                  <div class="flex items-center justify-between">
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-violet-600" />语音情绪 (20%)</span>
                    <span class="font-bold">{{ getVoiceScore(fusionReportData.voiceData) }} <span class="text-xs text-slate-400">/ 100</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-violet-500" :style="{ width: `${Math.min(100, getVoiceScore(fusionReportData.voiceData))}%` }" /></div>
                </div>
                <div>
                  <div class="flex items-center justify-between">
                    <span class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"><Activity class="h-4 w-4 text-cyan-600" />表情识别 (30%)</span>
                    <span class="font-bold">{{ getExpressionScore(fusionReportData.expressionData) }} <span class="text-xs text-slate-400">/ 100</span></span>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-cyan-500" :style="{ width: `${Math.min(100, getExpressionScore(fusionReportData.expressionData))}%` }" /></div>
                </div>
              </div>
            </div>

            <div class="mt-5 grid gap-3 md:grid-cols-2">
              <div class="rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50 p-4 dark:border-blue-950 dark:from-blue-950/30 dark:to-indigo-950/30">
                <h3 class="text-sm font-bold text-blue-800 dark:text-blue-200">心理调节建议</h3>
                <ul class="mt-3 space-y-2 text-xs leading-5 text-slate-700 dark:text-slate-200">
                  <li>每天进行10分钟正念冥想练习</li>
                  <li>保持规律作息，确保7-8小时睡眠</li>
                  <li>适度运动，每周3次有氧运动</li>
                </ul>
              </div>
              <div class="rounded-xl border border-amber-100 bg-gradient-to-br from-amber-50 to-orange-50 p-4 dark:border-amber-950 dark:from-amber-950/30 dark:to-orange-950/30">
                <h3 class="text-sm font-bold text-amber-800 dark:text-amber-200">专业干预建议</h3>
                <ul class="mt-3 space-y-2 text-xs leading-5 text-slate-700 dark:text-slate-200">
                  <li>建议预约心理咨询师进行深度评估</li>
                  <li>考虑认知行为疗法（CBT）干预</li>
                  <li>定期复查，建议2周后重新评估</li>
                </ul>
              </div>
            </div>

            <div class="mt-5 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 p-4 dark:border-emerald-950 dark:from-emerald-950/30 dark:via-teal-950/30 dark:to-cyan-950/30" data-testid="profile-fusion-professional-advice">
              <h3 class="font-bold text-emerald-800 dark:text-emerald-200">智能诊断结论</h3>
              <p class="mt-3 whitespace-pre-line rounded-lg bg-white/70 p-3 text-sm leading-7 text-slate-700 dark:bg-slate-950/40 dark:text-slate-200">{{ professionalAdvice }}</p>
            </div>
          </div>
        </section>
      </div>

      <div v-if="reportHistoryOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4" data-testid="profile-fusion-history-dialog">
        <section class="flex max-h-[86vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl bg-white p-5 shadow-xl dark:bg-slate-950">
          <div class="flex shrink-0 items-center justify-between">
            <h2 class="text-xl font-black text-slate-900 dark:text-white">历史记录</h2>
            <button class="grid h-9 w-9 place-items-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-900" data-testid="profile-fusion-history-close" @click="reportHistoryOpen = false"><X class="h-5 w-5 text-slate-400" /></button>
          </div>
          <div class="mt-4 space-y-2 overflow-y-auto pr-1">
            <div v-if="reportHistoryLoading" class="flex justify-center rounded-xl bg-slate-50 py-10 text-slate-400 dark:bg-slate-900" data-testid="profile-fusion-history-loading">
              <Activity class="h-6 w-6 animate-spin" />
            </div>
            <button
              v-else
              v-for="item in state.assessments.slice(0, 8)"
              :key="item.id"
              class="w-full rounded-xl border p-3 text-left text-sm transition hover:border-primary/40 hover:bg-primary/5 dark:border-slate-800"
              :class="selectedProfileReport?.id === item.id ? 'border-primary/60 bg-primary/10 dark:bg-primary/10' : 'border-slate-100 bg-slate-50 dark:bg-slate-900'"
              data-testid="profile-fusion-history-item"
              @click="selectedHistoryId = item.id; reportHistoryOpen = false"
            >
              <span class="font-bold text-slate-800 dark:text-white">{{ item.createdAt }}</span>
              <span class="ml-2 text-slate-500">{{ item.overall.label }} · {{ item.overall.score }}</span>
            </button>
            <p v-if="!reportHistoryLoading && state.assessments.length === 0" class="rounded-xl bg-slate-50 p-4 text-center text-sm text-slate-500 dark:bg-slate-900">
              暂无历史记录
            </p>
          </div>
        </section>
      </div>

      <div v-if="activeReport" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4" data-testid="profile-fusion-subreport-dialog">
        <section class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[20px] bg-white shadow-xl dark:bg-slate-950">
          <header
            class="flex items-center justify-between px-5 py-4 text-white"
            :class="activeReport === 'scale' ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600' : activeReport === 'voice' ? 'bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600' : 'bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600'"
          >
            <div>
              <h2 class="text-xl font-bold">{{ activeReport === 'scale' ? '量表评估报告' : activeReport === 'voice' ? '语音情绪报告' : '表情识别报告' }}</h2>
              <p class="text-xs text-white/80">{{ activeReport === 'scale' ? 'PHQ-9 抑郁症筛查量表详细得分与分析' : activeReport === 'voice' ? '基于声学特征的情绪状态分析' : '基于面部微表情的情绪状态分析' }}</p>
            </div>
            <button @click="activeReport = null"><X class="h-5 w-5" /></button>
          </header>

          <div v-if="activeReport === 'scale'" class="space-y-5 p-5" data-testid="profile-fusion-scale-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-600 dark:text-slate-300">PHQ-9 总分</span>
                <span class="rounded-full px-3 py-1 text-xs font-bold text-white" :class="profileRiskClass">{{ profileRiskText }}</span>
              </div>
              <p class="mt-3 text-4xl font-black text-slate-900 dark:text-white">{{ getScaleScore(fusionReportData.scaleData) }} <span class="text-lg text-slate-400">/ 27</span></p>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div v-for="item in scaleDimensionScores" :key="item.label" class="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                <p class="text-xs text-slate-500">{{ item.label }}</p>
                <p class="mt-1 text-lg font-bold text-slate-800 dark:text-white">{{ item.score }} <span class="text-xs text-slate-400">/ {{ item.max || 3 }}</span></p>
              </div>
            </div>
          </div>

          <div v-else-if="activeReport === 'voice'" class="space-y-5 p-5" data-testid="profile-fusion-voice-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <p class="text-4xl font-black text-slate-900 dark:text-white">{{ getVoiceScore(fusionReportData.voiceData) }} <span class="text-lg text-slate-400">/ 100</span></p>
              <p class="mt-3 text-sm leading-6 text-slate-500">
                {{ hasVoiceReport ? (fusionReportData.voiceData?.analysis || fusionReportData.voiceData?.depression_analysis || '已读取语音情绪结果。') : '暂无语音情绪报告，请先完成语音评估。' }}
              </p>
            </div>
            <div v-if="hasVoiceReport" class="grid grid-cols-2 gap-3">
              <div v-for="item in voiceEmotionItems" :key="item.label" class="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                <p class="text-xs text-slate-500">{{ item.label }}</p>
                <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-[#7A3EF4]" :style="{ width: `${Math.round(item.value * 100)}%` }" /></div>
              </div>
            </div>
            <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900">缺少 speech-recognition 转写、声学指标或情绪向量，不能展示语音分报告。</p>
          </div>

          <div v-else class="space-y-5 p-5" data-testid="profile-fusion-expression-detail">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
              <p class="text-4xl font-black text-slate-900 dark:text-white">{{ getExpressionScore(fusionReportData.expressionData) }} <span class="text-lg text-slate-400">/ 100</span></p>
              <p class="mt-3 text-sm leading-6 text-slate-500">
                {{ hasExpressionReport ? (fusionReportData.expressionData?.analysis_report || '已读取面部视觉分析结果。') : '暂无表情识别报告，请先完成面部评估。' }}
              </p>
            </div>
            <div v-if="hasExpressionReport" class="space-y-3">
              <div v-for="item in expressionRadarItems" :key="item.key" class="flex items-center gap-3">
                <span class="w-12 text-sm text-slate-600 dark:text-slate-300">{{ item.label }}</span>
                <div class="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-full rounded-full bg-cyan-500" :style="{ width: `${Math.round(item.value * 100)}%` }" /></div>
                <span class="w-10 text-right text-sm font-bold text-slate-700 dark:text-slate-200">{{ Math.round(item.value * 100) }}%</span>
              </div>
            </div>
            <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-900">缺少 multimodal-analysis 返回的 9 维情绪雷达或分析报告，不能展示表情分报告。</p>
          </div>
          <div class="flex justify-end gap-3 border-t border-slate-100 px-5 py-4 dark:border-slate-800">
            <button class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200" @click="exportProfileFusionReport('pdf')">
              <FileText class="mr-2 inline h-4 w-4" />
              导出报告
            </button>
            <button class="rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white dark:bg-white dark:text-slate-900" @click="activeReport = null">
              关闭
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes profile-report-loading {
  from {
    width: 0%;
  }
  to {
    width: 100%;
  }
}
</style>
