import { computed, reactive } from 'vue'
import {
  meditationTracks,
} from '@/data/static'
import { useAuthSession } from '@/composables/useAuthSession'
import {
  createEmotionDiary,
  createRiskAlert,
  getAssessments,
  getEmotionDiaries,
  getProfile,
  syncReport,
  updateEmotionDiary,
} from '@/db/api'
import type {
  AppProfile,
  Assessment,
  AssessmentRecord,
  DiaryEntry,
  EmotionDiary,
  MeditationTrack,
  MoodLevel,
  Profile,
} from '@/types'

interface AppState {
  currentAccountId: string | null
  currentAccountRole: string
  currentAccountCreatedAt: string
  profile: AppProfile
  diaries: DiaryEntry[]
  assessments: AssessmentRecord[]
}

const defaultState = (): AppState => ({
  currentAccountId: null,
  currentAccountRole: '',
  currentAccountCreatedAt: '',
  profile: { phoneNumber: '', username: '' },
  diaries: [],
  assessments: [],
})

const state = reactive<AppState>(defaultState())

let bootstrapPromise: Promise<void> | null = null

const formatDateTime = (value?: string | null) => {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const mapProfileToAppProfile = (
  profile:
    | ({
        username: string
        phone?: string | null
      } & Partial<Profile>)
    | null
    | undefined,
): AppProfile => ({
  phoneNumber: profile?.phone || '',
  username: profile?.username || '',
})

const mapDiary = (record: EmotionDiary): DiaryEntry => ({
  id: String(record.id),
  date: record.diary_date,
  mood: record.emotion_level as MoodLevel,
  content: record.content || '',
  triggers: record.tags || [],
  images: record.image_urls || [],
  aiAnalysis: record.ai_analysis as DiaryEntry['aiAnalysis'],
  createdAt: record.created_at,
})

const normalizeSection = (value: any, fallbackLabel: string): AssessmentRecord['scale'] => ({
  score: Number(value?.score ?? value?.depression_risk_score ?? 0),
  label: String(value?.label ?? value?.risk_level_text ?? fallbackLabel),
  summary: String(value?.summary ?? value?.analysis ?? value?.advice ?? '暂无分析摘要'),
})

const mapAssessment = (record: Assessment): AssessmentRecord => {
  const report = record.report || {}
  const scale = normalizeSection(report.scaleData || report.scale, '量表评估')
  const voice = normalizeSection(report.voiceData || report.voice, '语音分析')
  const expression = normalizeSection(report.expressionData || report.expression, '表情分析')
  const overall = normalizeSection(
    report.overall || {
      score: record.score ?? 0,
      label: record.assessment_type === 'assessment_package_report'
        ? '五段式综合测评报告'
        : record.assessment_type === 'fusion_report'
          ? 'AI多模态报告'
          : '评估结果',
      summary: report.summary || report.overallSummary || '已生成评估结果',
    },
    '综合评估',
  )

  return {
    id: String(record.id),
    createdAt: formatDateTime(record.created_at),
    scale,
    voice,
    expression,
    overall,
    report,
  }
}

async function loadUserWorkspace(userId: string) {
  const [profile, diaries, assessments] = await Promise.all([
    getProfile(userId),
    getEmotionDiaries(userId, 100),
    getAssessments(userId, 100),
  ])

  state.profile = mapProfileToAppProfile(profile)
  state.currentAccountCreatedAt = profile?.created_at || state.currentAccountCreatedAt
  state.diaries = diaries.map(mapDiary)
  state.assessments = assessments.map(mapAssessment)
}

async function bootstrapState(force = false) {
  if (!force && bootstrapPromise) {
    await bootstrapPromise
    return
  }

  const { state: authState, ensureInitialized } = useAuthSession()

  bootstrapPromise = (async () => {
    await ensureInitialized()

    if (!authState.user) {
      Object.assign(state, defaultState())
      return
    }

    state.currentAccountId = authState.user.id
    state.currentAccountRole = authState.profile?.role || authState.user.user_metadata?.role || 'user'
    state.currentAccountCreatedAt = authState.profile?.created_at || ''
    state.profile = mapProfileToAppProfile(authState.profile)

    await loadUserWorkspace(authState.user.id)
  })()

  try {
    await bootstrapPromise
  } finally {
    bootstrapPromise = null
  }
}

export const useAppState = () => {
  const sortedDiaries = computed(() =>
    [...state.diaries].sort((a, b) => {
      const bTime = new Date(b.createdAt ?? b.date).getTime()
      const aTime = new Date(a.createdAt ?? a.date).getTime()
      return bTime - aTime
    }),
  )

  const saveDiary = (entry: DiaryEntry) => {
    const index = state.diaries.findIndex((item) => item.id === entry.id)
    if (index >= 0) {
      state.diaries[index] = entry
      return
    }
    state.diaries.unshift(entry)
  }

  const loadEmotionRecords = async () => {
    await bootstrapState()
  }

  const createEmotionRecord = async (payload: {
    date: string
    mood: MoodLevel
    content: string
    triggers: string[]
    images?: string[]
  }) => {
    if (!state.currentAccountId) return undefined

    const diaryPayload = {
      emotion_level: payload.mood,
      content: payload.content,
      tags: payload.triggers,
      image_urls: payload.images || [],
    }

    const existing = state.diaries.find((item) => item.date === payload.date)
    const created = existing
      ? await updateEmotionDiary(existing.id, diaryPayload)
      : await createEmotionDiary({
          user_id: state.currentAccountId,
          diary_date: payload.date,
          ...diaryPayload,
        })

    const mapped = mapDiary(created)
    saveDiary(mapped)
    return mapped
  }

  const addAssessment = async (record: AssessmentRecord) => {
    state.assessments.unshift(record)

    if (!state.currentAccountId) {
      return
    }

    const scaleRaw = record.scale.score <= 27 ? record.scale.score : Math.round((record.scale.score / 100) * 27)
    const normalizedScores = {
      scale: record.scale.score,
      voice: record.voice.score,
      expression: record.expression.score,
    }
    const weights = { scale: 0.5, voice: 0.2, expression: 0.3 }
    const sourceReport = record.report || {}
    let syncedAssessmentId: string | undefined

    try {
      syncedAssessmentId = await syncReport({
        user_id: state.currentAccountId,
        score: record.overall.score,
        risk_level: record.overall.score,
        conversation_history: sourceReport.scaleData?.conversationHistory || sourceReport.scaleData?.conversation_history || [],
        report_details: {
          scaleRaw,
          normalizedScores,
          ...sourceReport,
          scaleData: sourceReport.scaleData || record.scale,
          voiceData: sourceReport.voiceData || record.voice,
          expressionData: sourceReport.expressionData || record.expression,
          overall: record.overall,
          advice: record.overall.summary,
          generatedAt: new Date().toISOString(),
        },
        weights,
      })
    } catch (error) {
      const index = state.assessments.findIndex((item) => item.id === record.id)
      if (index >= 0) {
        state.assessments.splice(index, 1)
      }
      throw error
    }

    if (syncedAssessmentId) {
      const assessments = await getAssessments(state.currentAccountId, 1)
      const latest = assessments[0]
      if (latest) {
        const mapped = mapAssessment(latest)
        const index = state.assessments.findIndex((item) => item.id === record.id)
        if (index >= 0) {
          state.assessments[index] = mapped
        }
      }
    }

    const requiresAlert =
      record.overall.score >= 40 ||
      scaleRaw >= 10 ||
      (record.voice.score >= 60 && record.expression.score >= 60)
    if (requiresAlert) {
      try {
        const riskLevel10 = Math.min(10, Math.max(1, Math.ceil(record.overall.score / 10)))
        const alertType =
          record.overall.score >= 80 || scaleRaw >= 20
            ? '极高风险预警'
            : record.overall.score >= 60 || scaleRaw >= 15
              ? '高风险预警'
              : '中风险预警'
        await createRiskAlert({
          patient_id: state.currentAccountId,
          alert_type: alertType,
          risk_level: riskLevel10,
          description: `融合风险分值 ${record.overall.score}/100，量表 ${scaleRaw}/27，语音 ${record.voice.score}/100，表情 ${record.expression.score}/100。建议管理员尽快查看评估详情并进行随访。`,
          data_source: 'fusion_report',
          source_id: syncedAssessmentId,
          is_handled: false,
        })
      } catch {
        // Match xinyu-care: alert push failure must not invalidate the report.
      }
    }
  }

  const refreshCurrentAccountProfile = async () => {
    await bootstrapState(true)
  }

  const refreshAssessments = async () => {
    if (!state.currentAccountId) return []
    const assessments = await getAssessments(state.currentAccountId, 100)
    state.assessments = assessments.map(mapAssessment)
    return state.assessments
  }

  void bootstrapState().catch(() => undefined)

  return {
    state,
    meditationTracks: meditationTracks as MeditationTrack[],
    sortedDiaries,
    saveDiary,
    loadEmotionRecords,
    createEmotionRecord,
    addAssessment,
    refreshCurrentAccountProfile,
    refreshAssessments,
  }
}
