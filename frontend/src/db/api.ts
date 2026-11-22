import type {
  Assessment,
  AssessmentPublishTask,
  AssessmentPublishAssignee,
  AssessmentPackageReport,
  BrainInterventionReport,
  BrainInterventionReportPayload,
  ChatMessage,
  CommunityComment,
  CommunityPost,
  Department,
  DoctorPatient,
  EmotionDiary,
  HealingContent,
  HuaxinyunScaleImportResult,
  InterventionDailySummary,
  InterventionMaterial,
  InterventionPlanTemplate,
  InterventionPublishBatch,
  InterventionTodayResponse,
  KnowledgeBase,
  MultimodalMessage,
  Profile,
  RiskAlert,
  ScaleDistributionPlan,
  ScaleDistributionRecord,
  ScaleSurvey,
  NeuropsychRecord,
  NeuropsychTest,
  UserHealingRecord,
  WearableData,
} from '@/types'
import {
  apiRequest,
  callRpc,
  deleteRows,
  deleteStorageFiles,
  insertRow,
  invokeFunction,
  publicStorageUrl,
  selectMaybeSingle,
  selectRows,
  updateRow,
  uploadStorageFile,
  type FilterCondition,
  type OrderCondition,
} from '@/lib/backend-api'

const assessmentFingerprint = (assessment: any) => {
  if (assessment.assessment_type !== 'fusion_report') return assessment.id
  const createdAt = assessment.created_at ? new Date(assessment.created_at).getTime() : 0
  const timeBucket = createdAt ? Math.floor(createdAt / (2 * 60 * 1000)) : assessment.id
  return [
    assessment.user_id,
    assessment.assessment_type,
    assessment.score ?? '',
    assessment.report?.scaleData?.score ?? '',
    assessment.report?.voiceData?.score ?? '',
    assessment.report?.expressionData?.depression_risk_score ?? '',
    timeBucket,
  ].join('|')
}

const dedupeAssessments = <T extends any[]>(assessments: T): T => {
  const seen = new Set<string>()
  return assessments.filter((assessment: any) => {
    const key = assessmentFingerprint(assessment)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  }) as T
}

const eq = (field: string, value: unknown): FilterCondition => ({ op: 'eq', field, value })
const gte = (field: string, value: unknown): FilterCondition => ({ op: 'gte', field, value })
const lte = (field: string, value: unknown): FilterCondition => ({ op: 'lte', field, value })
const desc = (field: string): OrderCondition => ({ field, ascending: false })
const asc = (field: string): OrderCondition => ({ field, ascending: true })

const normalizeCode = (code: string) =>
  code
    .trim()
    .replace(/[\uFF10-\uFF19\uFF21-\uFF3A\uFF41-\uFF5A]/g, (ch) =>
      String.fromCharCode(ch.charCodeAt(0) - 0xfee0),
    )

async function listRows<T>(
  table: string,
  options: {
    filters?: FilterCondition[]
    orders?: OrderCondition[]
    limit?: number
    count?: boolean
    head?: boolean
  } = {},
) {
  const envelope = await selectRows<T>(table, options)
  return {
    rows: Array.isArray(envelope.data) ? envelope.data : [],
    count: envelope.count || 0,
  }
}

export const getProfile = async (userId: string) =>
  selectMaybeSingle<Profile>('profiles', { filters: [eq('id', userId)] })

export const updateProfile = async (userId: string, updates: Partial<Profile>) =>
  updateRow<Profile>('profiles', updates as Record<string, unknown>, [eq('id', userId)])

export const getAllProfiles = async () => {
  const { rows } = await listRows<Profile>('profiles', { orders: [desc('created_at')] })
  return rows
}

export const getDepartments = async (auth = true) => {
  const envelope = await apiRequest<{ data: Department[] }>('/api/departments', { auth })
  return envelope.data || []
}

export const createDepartment = async (payload: Pick<Department, 'name'> & Partial<Department>) => {
  const envelope = await apiRequest<{ data: Department }>('/api/departments', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const updateDepartment = async (id: string, payload: Partial<Department>) => {
  const envelope = await apiRequest<{ data: Department }>(`/api/departments/${id}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const deleteDepartment = async (id: string) => {
  const envelope = await apiRequest<{ data: { deleted: boolean; id: string } }>(`/api/departments/${id}`, {
    method: 'DELETE',
  })
  return envelope.data
}

export const updateSuperAdminAccount = async (payload: { username: string; password?: string }) => {
  const envelope = await apiRequest<{ data: any }>('/api/auth/super-admin/account', {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const getEmotionDiaries = async (userId: string, limit = 30) => {
  const { rows } = await listRows<EmotionDiary>('emotion_diaries', {
    filters: [eq('user_id', userId)],
    orders: [desc('diary_date')],
    limit,
  })
  return rows
}

export const getEmotionDiaryByDate = async (userId: string, date: string) =>
  selectMaybeSingle<EmotionDiary>('emotion_diaries', {
    filters: [eq('user_id', userId), eq('diary_date', date)],
  })

export const createEmotionDiary = async (diary: Partial<EmotionDiary>) =>
  insertRow<EmotionDiary>('emotion_diaries', diary as Record<string, unknown>, {
    upsert: true,
    onConflict: 'user_id,diary_date',
  })

export const updateEmotionDiary = async (id: string, updates: Partial<EmotionDiary>) =>
  updateRow<EmotionDiary>('emotion_diaries', updates as Record<string, unknown>, [eq('id', id)])

export const deleteEmotionDiary = async (id: string) => {
  await deleteRows('emotion_diaries', [eq('id', id)])
}

export const getAssessments = async (userId: string, limit = 10) => {
  const { rows } = await listRows<Assessment>('assessments', {
    filters: [eq('user_id', userId)],
    orders: [desc('created_at')],
    limit,
  })
  return dedupeAssessments(rows).slice(0, limit)
}

export const getAllAssessments = async (limit = 1000) => {
  const { rows } = await listRows<Assessment>('assessments', { orders: [desc('created_at')], limit })
  return dedupeAssessments(rows).slice(0, limit)
}

export const getAllEmotionDiaries = async (limit = 1000) => {
  const { rows } = await listRows<EmotionDiary>('emotion_diaries', {
    orders: [desc('diary_date')],
    limit,
  })
  return rows
}

export const getAssessmentById = async (id: string) =>
  selectMaybeSingle<Assessment>('assessments', { filters: [eq('id', id)] })

export const createAssessment = async (assessment: Partial<Assessment>) =>
  insertRow<Assessment>('assessments', assessment as Record<string, unknown>)

export const updateAssessment = async (id: string, updates: Partial<Assessment>) =>
  updateRow<Assessment>('assessments', updates as Record<string, unknown>, [eq('id', id)])

export const getWearableData = async (userId: string, limit = 30) => {
  const { rows } = await listRows<WearableData>('wearable_data', {
    filters: [eq('user_id', userId)],
    orders: [desc('record_date')],
    limit,
  })
  return rows
}

export const getWearableDataByDateRange = async (userId: string, startDate: string, endDate: string) => {
  const { rows } = await listRows<WearableData>('wearable_data', {
    filters: [eq('user_id', userId), gte('record_date', startDate), lte('record_date', endDate)],
    orders: [asc('record_date')],
  })
  return rows
}

export const getLatestWearableData = async (userId: string) =>
  selectMaybeSingle<WearableData>('wearable_data', {
    filters: [eq('user_id', userId)],
    orders: [desc('record_date')],
  })

export const createWearableData = async (wearableData: Partial<WearableData>) =>
  insertRow<WearableData>('wearable_data', wearableData as Record<string, unknown>)

export const updateWearableData = async (id: string, updates: Partial<WearableData>) =>
  updateRow<WearableData>('wearable_data', updates as Record<string, unknown>, [eq('id', id)])

export const upsertWearableData = async (wearableData: Partial<WearableData>) =>
  insertRow<WearableData>('wearable_data', wearableData as Record<string, unknown>, {
    upsert: true,
    onConflict: 'user_id,record_date',
  })

export const getHealingContents = async (category?: string) => {
  const filters = [eq('is_active', true)]
  if (category) filters.push(eq('category', category))
  const { rows } = await listRows<HealingContent>('healing_contents', {
    filters,
    orders: [desc('created_at')],
  })
  return rows
}

export const createHealingRecord = async (record: Partial<UserHealingRecord>) =>
  insertRow<UserHealingRecord>('user_healing_records', record as Record<string, unknown>)

export const getHealingRecords = async (userId: string, limit = 20) => {
  const { rows } = await listRows<UserHealingRecord>('user_healing_records', {
    filters: [eq('user_id', userId)],
    orders: [desc('created_at')],
    limit,
  })
  return rows
}

export const getCommunityPosts = async (limit = 20) => {
  const { rows } = await listRows<CommunityPost>('community_posts', {
    filters: [eq('is_hidden', false)],
    orders: [desc('is_pinned'), desc('created_at')],
    limit,
  })
  return rows
}

export const createCommunityPost = async (post: Partial<CommunityPost>) => {
  const payload = {
    ...post,
    anonymous_name: post.anonymous_name || post.anonymous_nickname || '匿名用户',
  }
  return insertRow<CommunityPost>('community_posts', payload as Record<string, unknown>)
}

export const getCommunityComments = async (postId: string) => {
  const { rows } = await listRows<CommunityComment>('community_comments', {
    filters: [eq('post_id', postId)],
    orders: [asc('created_at')],
  })
  return rows
}

export const getCommunityPostCommentCount = async (postId: string) => {
  const { count } = await listRows<CommunityComment>('community_comments', {
    filters: [eq('post_id', postId)],
    head: true,
    count: true,
  })
  return count
}

export const createCommunityComment = async (comment: Partial<CommunityComment>) =>
  insertRow<CommunityComment>('community_comments', comment as Record<string, unknown>)

export const deleteCommunityPost = async (postId: string, userId: string) => {
  const post = await selectMaybeSingle<CommunityPost>('community_posts', { filters: [eq('id', postId)] })
  if (!post || post.user_id !== userId) {
    throw new Error('无权删除此帖子')
  }
  await deleteRows('community_posts', [eq('id', postId)])
}

export const deleteHealingContent = async (contentId: string) => {
  await deleteRows('healing_contents', [eq('id', contentId)])
}

export const togglePostLike = async (postId: string, userId: string) => {
  const existing = await selectMaybeSingle<{ id: string }>('post_likes', {
    filters: [eq('post_id', postId), eq('user_id', userId)],
  })
  if (existing) {
    await deleteRows('post_likes', [eq('id', existing.id)])
    return false
  }
  await insertRow('post_likes', { post_id: postId, user_id: userId })
  return true
}

export const createMeditationSession = async (session: {
  user_id: string
  content_id: string
  duration: number
  completed?: boolean
  mood_before?: string
  mood_after?: string
  notes?: string
}) => insertRow('meditation_sessions', session)

export const syncReport = async (reportData: {
  user_id: string
  assessment_id?: string
  score: number
  risk_level: number
  conversation_history?: any[]
  report_details: any
  weights: { scale: number; voice: number; expression: number }
}) => {
  let assessmentId = reportData.assessment_id
  const conversationHistory =
    reportData.conversation_history ?? reportData.report_details?.scaleData?.conversationHistory ?? []

  if (assessmentId) {
    await updateAssessment(assessmentId, {
      score: reportData.score,
      risk_level: reportData.risk_level,
      conversation_history: conversationHistory,
      report: {
        ...reportData.report_details,
        weights: reportData.weights,
        synced_at: new Date().toISOString(),
      },
    })
    return assessmentId
  }

  const lowerBound = new Date(Date.now() - 2 * 60 * 1000).toISOString()
  const { rows: recent } = await listRows<Assessment>('assessments', {
    filters: [
      eq('user_id', reportData.user_id),
      eq('assessment_type', 'fusion_report'),
      gte('created_at', lowerBound),
    ],
    orders: [desc('created_at')],
    limit: 5,
  })

  const duplicate = recent.find((item: any) => {
    const report = item.report || {}
    return (
      report.scaleData?.score === reportData.report_details?.scaleData?.score &&
      report.voiceData?.score === reportData.report_details?.voiceData?.score &&
      report.expressionData?.depression_risk_score ===
        reportData.report_details?.expressionData?.depression_risk_score
    )
  })

  if (duplicate) {
    await updateAssessment(duplicate.id, {
      score: reportData.score,
      risk_level: reportData.risk_level,
      conversation_history: conversationHistory,
      report: {
        ...reportData.report_details,
        weights: reportData.weights,
        synced_at: new Date().toISOString(),
      },
    })
    return duplicate.id
  }

  const created = await createAssessment({
    user_id: reportData.user_id,
    assessment_type: 'fusion_report',
    score: reportData.score,
    risk_level: reportData.risk_level,
    conversation_history: conversationHistory,
    report: {
      ...reportData.report_details,
      weights: reportData.weights,
      synced_at: new Date().toISOString(),
    },
  })
  return created?.id
}

export const getReportHistory = async (userId: string, filters?: { startDate?: string; endDate?: string }) => {
  const queryFilters = [eq('user_id', userId)]
  if (filters?.startDate && filters?.endDate) {
    queryFilters.push(gte('created_at', filters.startDate), lte('created_at', filters.endDate))
  }
  const { rows } = await listRows<Assessment>('assessments', {
    filters: queryFilters,
    orders: [desc('created_at')],
  })
  return rows
}

export const getMeditationSessions = async (userId: string, limit = 50) => {
  const { rows } = await listRows<any>('meditation_sessions', {
    filters: [eq('user_id', userId)],
    orders: [desc('created_at')],
    limit,
  })
  return rows
}

export const getMeditationStats = async (userId: string) => {
  const { rows } = await listRows<{ duration: number; completed: boolean }>('meditation_sessions', {
    filters: [eq('user_id', userId), eq('completed', true)],
  })
  const totalMinutes = rows.reduce((sum, item) => sum + Math.floor((item.duration || 0) / 60), 0)
  return { totalMinutes, totalSessions: rows.length }
}

export const toggleFavorite = async (userId: string, contentId: string) => {
  const existing = await selectMaybeSingle<{ id: string }>('user_favorites', {
    filters: [eq('user_id', userId), eq('content_id', contentId)],
  })
  if (existing) {
    await deleteRows('user_favorites', [eq('id', existing.id)])
    return false
  }
  await insertRow('user_favorites', { user_id: userId, content_id: contentId })
  return true
}

export const getUserFavorites = async (userId: string) => {
  const { rows } = await listRows<any>('user_favorites', {
    filters: [eq('user_id', userId)],
    orders: [desc('created_at')],
  })
  return rows
}

export const isFavorited = async (userId: string, contentId: string) =>
  !!(await selectMaybeSingle('user_favorites', {
    filters: [eq('user_id', userId), eq('content_id', contentId)],
  }))

export const getPostCategories = async () => {
  const { rows } = await listRows<any>('post_categories', { orders: [asc('created_at')] })
  return rows
}

export const getCommunityPostsByCategory = async (categoryId?: string, limit = 20) => {
  const filters = categoryId ? [eq('category_id', categoryId)] : undefined
  const { rows } = await listRows<CommunityPost>('community_posts', {
    filters,
    orders: [desc('created_at')],
    limit,
  })
  return rows
}

export const getRecoveryStories = async (limit = 10) => {
  const { rows } = await listRows<CommunityPost>('community_posts', {
    filters: [eq('is_recovery_story', true)],
    orders: [desc('created_at')],
    limit,
  })
  return rows
}

export const incrementViewCount = async (contentId: string) => {
  await callRpc('increment_view_count', { content_id: contentId })
}

export const incrementLikeCount = async (contentId: string) => {
  await callRpc('increment_like_count', { content_id: contentId })
}

export const getDoctorPatients = async (_doctorId: string) => {
  const { rows } = await listRows<DoctorPatient>('doctor_patients', { orders: [desc('created_at')] })
  return rows
}

export const addPatient = async (doctorId: string, patientId: string, notes?: string) =>
  insertRow<DoctorPatient>('doctor_patients', { doctor_id: doctorId, patient_id: patientId, notes })

export const getRiskAlerts = async (isHandled?: boolean) => {
  const filters = isHandled === undefined ? undefined : [eq('is_handled', isHandled)]
  const { rows } = await listRows<RiskAlert>('risk_alerts', { filters, orders: [desc('created_at')] })
  return rows
}

export const handleRiskAlert = async (alertId: string, handledBy: string, notes?: string) =>
  updateRow<RiskAlert>(
    'risk_alerts',
    {
      is_handled: true,
      handled_by: handledBy,
      handled_at: new Date().toISOString(),
      notes,
    },
    [eq('id', alertId)],
  )

export const createRiskAlert = async (alert: Partial<RiskAlert>) => {
  if (alert.source_id) {
    const existing = await selectMaybeSingle<RiskAlert>('risk_alerts', {
      filters: [eq('source_id', alert.source_id), eq('data_source', alert.data_source || 'fusion_report')],
    })
    if (existing) {
      return existing
    }
  }
  return insertRow<RiskAlert>('risk_alerts', alert as Record<string, unknown>)
}

export const getKnowledgeBase = async (category?: string) => {
  const filters = [eq('is_active', true)]
  if (category) filters.push(eq('category', category))
  const { rows } = await listRows<KnowledgeBase>('knowledge_base', {
    filters,
    orders: [desc('created_at')],
  })
  return rows
}

export const createKnowledge = async (knowledge: Partial<KnowledgeBase>) =>
  insertRow<KnowledgeBase>('knowledge_base', knowledge as Record<string, unknown>)

export const updateKnowledge = async (id: string, updates: Partial<KnowledgeBase>) =>
  updateRow<KnowledgeBase>('knowledge_base', updates as Record<string, unknown>, [eq('id', id)])

export const deleteKnowledge = async (id: string) => {
  await deleteRows('knowledge_base', [eq('id', id)])
}

export const chatCompletion = async (messages: ChatMessage[], enableThinking = false) =>
  invokeFunction<any>('chat-completion', { messages, enable_thinking: enableThinking })

export const multimodalAnalysis = async (messages: MultimodalMessage[], enableThinking = false) =>
  invokeFunction<any>('multimodal-analysis', { messages, enable_thinking: enableThinking })

export const speechRecognition = async (
  audioBase64: string,
  format: 'wav' | 'm4a' | 'webm' | 'ogg' | 'mp3',
  rate: 16000 | 8000,
  len: number,
) =>
  invokeFunction<any>('speech-recognition', {
    input_audio: {
      data: audioBase64,
      format,
    },
    format,
    rate,
    cuid: crypto.randomUUID(),
    speech: audioBase64,
    len,
  })

export const ragRetrieval = async (
  query: string,
  conversationHistory: ChatMessage[],
  assessmentType = 'PHQ-9',
) =>
  invokeFunction<any>('rag-retrieval', {
    query,
    conversation_history: conversationHistory,
    assessment_type: assessmentType,
  })

export const multimodalFusion = async (params: {
  text_analysis?: any
  image_analysis?: any
  voice_analysis?: any
  video_analysis?: any
  user_id: string
  assessment_id: string
}) => invokeFunction<any>('multimodal-fusion', params)

export const uploadKnowledgeDocument = async (file: File, category: string) => {
  const timestamp = Date.now()
  const sanitizedName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_')
  const filePath = `${category}/${timestamp}_${sanitizedName}`
  const data = await uploadStorageFile('knowledge-documents', filePath, file)
  return { path: data.path, name: file.name, size: file.size, type: file.type }
}

export const deleteKnowledgeDocument = async (filePath: string) => {
  await deleteStorageFiles('knowledge-documents', [filePath])
}

export const getKnowledgeDocumentUrl = (filePath: string) =>
  publicStorageUrl('knowledge-documents', filePath)

export interface DoctorVerificationCode {
  id: string
  code: string
  is_permanent: boolean
  is_used: boolean
  used_by?: string
  used_at?: string
  created_by?: string
  created_at: string
  notes?: string
}

export const getVerificationCodes = async () => {
  const { rows } = await listRows<DoctorVerificationCode>('doctor_verification_codes', {
    orders: [desc('created_at')],
  })
  return rows
}

export const createVerificationCode = async (code: string, notes?: string, createdBy?: string) =>
  insertRow<DoctorVerificationCode>('doctor_verification_codes', {
    code,
    is_permanent: false,
    is_used: false,
    notes,
    created_by: createdBy,
  })

export const deleteVerificationCode = async (id: string) => {
  await deleteRows('doctor_verification_codes', [eq('id', id), eq('is_permanent', false)])
}

export const verifyCode = async (code: string) => {
  const data = await selectMaybeSingle<DoctorVerificationCode>('doctor_verification_codes', {
    filters: [eq('code', normalizeCode(code))],
  })
  if (!data) {
    return { valid: false, message: '验证码不存在' }
  }
  if (!data.is_permanent && data.is_used) {
    return { valid: false, message: '验证码已被使用' }
  }
  return { valid: true, data }
}

export const markCodeAsUsed = async (code: string, userId: string) => {
  await callRpc('verify_and_use_code', {
    p_code: normalizeCode(code),
    p_user_id: userId,
  })
}

export const getScaleSurveys = async () => {
  const envelope = await apiRequest<{ data: ScaleSurvey[] }>('/api/scale-assessments/surveys')
  return envelope.data || []
}

export const getScaleSurvey = async (surveyId: string) => {
  const envelope = await apiRequest<{ data: ScaleSurvey }>(`/api/scale-assessments/surveys/${surveyId}`)
  return envelope.data
}

export const reorderScaleSurveys = async (orders: { id: string; sort_order: number }[]) => {
  const envelope = await apiRequest<{ data: { updated: number } }>('/api/scale-assessments/surveys/reorder', {
    method: 'PUT',
    body: { orders },
  })
  return envelope.data
}

export const getFreeScaleSurveys = async () => {
  const envelope = await apiRequest<{ data: ScaleSurvey[] }>('/api/scale-assessments/free-surveys')
  return envelope.data || []
}

export const createScaleSurvey = async (payload: Partial<ScaleSurvey>) => {
  const envelope = await apiRequest<{ data: ScaleSurvey }>('/api/scale-assessments/surveys', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const updateScaleSurvey = async (surveyId: string, payload: Partial<ScaleSurvey>) => {
  const envelope = await apiRequest<{ data: ScaleSurvey }>(`/api/scale-assessments/surveys/${surveyId}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const publishScaleSurvey = async (surveyId: string) => {
  const envelope = await apiRequest<{ data: ScaleSurvey }>(`/api/scale-assessments/surveys/${surveyId}/publish`, {
    method: 'POST',
  })
  return envelope.data
}

export const cloneScaleSurvey = async (surveyId: string) => {
  const envelope = await apiRequest<{ data: ScaleSurvey }>(`/api/scale-assessments/surveys/${surveyId}/clone`, {
    method: 'POST',
  })
  return envelope.data
}

export const deleteScaleSurvey = async (surveyId: string) => {
  await apiRequest(`/api/scale-assessments/surveys/${surveyId}`, { method: 'DELETE' })
}

export const importHuaxinyunScaleSurveys = async (payload: {
  content: string
  dry_run?: boolean
  publish?: boolean
  overwrite?: boolean
  skip_invalid?: boolean
}) => {
  const envelope = await apiRequest<{ data: HuaxinyunScaleImportResult }>('/api/scale-assessments/import/huaxinyun', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const getScaleDistributionPlans = async () => {
  const envelope = await apiRequest<{ data: ScaleDistributionPlan[] }>('/api/scale-assessments/distribution-plans')
  return envelope.data || []
}

export const createScaleDistributionPlan = async (payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: ScaleDistributionPlan }>('/api/scale-assessments/distribution-plans', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const stopScaleDistributionPlan = async (planId: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionPlan }>(`/api/scale-assessments/distribution-plans/${planId}/stop`, {
    method: 'POST',
  })
  return envelope.data
}

export const getScaleResults = async (filters: Record<string, string> = {}) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord[] }>('/api/scale-assessments/results', {
    query: filters,
  })
  return envelope.data || []
}

export const getScaleResultDetail = async (recordId: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/results/${recordId}`)
  return envelope.data
}

export const recalculateScaleResult = async (recordId: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/results/${recordId}/recalculate`, {
    method: 'POST',
  })
  return envelope.data
}

export const exportScaleResults = async (unfinished = false) => {
  const endpoint = unfinished ? '/api/scale-assessments/results/export-unfinished' : '/api/scale-assessments/results/export'
  const envelope = await apiRequest<{ data: { filename: string; content: string } }>(endpoint)
  return envelope.data
}

export const importScaleAnswers = async (
  records: Array<{
    record_id: string
    answers: Array<{ questionId: string; questionType: string; myAnswer: string }>
  }>,
) => {
  const envelope = await apiRequest<{ data: { imported: number } }>('/api/scale-assessments/answers/import', {
    method: 'POST',
    body: { records },
  })
  return envelope.data
}

export const getMyScaleRecords = async () => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord[] }>('/api/scale-assessments/my-records')
  return envelope.data || []
}

export const getMyScaleRecord = async (recordId: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/records/${recordId}`)
  return envelope.data
}

export const startFreeScaleRecord = async (surveyCode: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/free/${surveyCode}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const startScaleRecord = async (recordId: string) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/records/${recordId}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const submitScaleRecord = async (
  recordId: string,
  answers: Array<{ questionId: string; questionType: string; myAnswer: string }>,
) => {
  const envelope = await apiRequest<{ data: ScaleDistributionRecord }>(`/api/scale-assessments/records/${recordId}/submit`, {
    method: 'POST',
    body: { answers },
  })
  return envelope.data
}

export const getNeuropsychTests = async () => {
  const envelope = await apiRequest<{ data: NeuropsychTest[] }>('/api/neuropsych-assessments/tests')
  return envelope.data || []
}

export const getFreeNeuropsychTests = async () => {
  const envelope = await apiRequest<{ data: NeuropsychTest[] }>('/api/neuropsych-assessments/free-tests')
  return envelope.data || []
}

export const updateNeuropsychTest = async (testId: string, payload: Partial<NeuropsychTest>) => {
  const envelope = await apiRequest<{ data: NeuropsychTest }>(`/api/neuropsych-assessments/tests/${testId}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const createNeuropsychDistributionPlan = async (payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: { id: string; created_records: number } }>('/api/neuropsych-assessments/distribution-plans', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const getNeuropsychResults = async (filters: Record<string, string> = {}) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord[] }>('/api/neuropsych-assessments/results', {
    query: filters,
  })
  return envelope.data || []
}

export const getNeuropsychResultDetail = async (recordId: string) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord }>(`/api/neuropsych-assessments/results/${recordId}`)
  return envelope.data
}

export const recalculateNeuropsychResult = async (recordId: string) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord }>(`/api/neuropsych-assessments/results/${recordId}/recalculate`, {
    method: 'POST',
  })
  return envelope.data
}

export const getMyNeuropsychRecords = async () => {
  const envelope = await apiRequest<{ data: NeuropsychRecord[] }>('/api/neuropsych-assessments/my-records')
  return envelope.data || []
}

export const startFreeNeuropsychRecord = async (testCode: string) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord }>(`/api/neuropsych-assessments/free/${testCode}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const startNeuropsychRecord = async (recordId: string) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord }>(`/api/neuropsych-assessments/records/${recordId}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const submitNeuropsychRecord = async (recordId: string, payload: { rawJson: string; rawCsv?: string; testCode?: string }) => {
  const envelope = await apiRequest<{ data: NeuropsychRecord }>(`/api/neuropsych-assessments/records/${recordId}/submit`, {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const getAssessmentPublishTasks = async () => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask[] }>('/api/assessment-publish-tasks')
  return envelope.data || []
}

export const getAssessmentPublishTask = async (taskId: string) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>(`/api/assessment-publish-tasks/${taskId}`)
  return envelope.data
}

export const createAssessmentPublishTask = async (payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>('/api/assessment-publish-tasks', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const updateAssessmentPublishTask = async (taskId: string, payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>(`/api/assessment-publish-tasks/${taskId}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const publishAssessmentPublishTask = async (taskId: string) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>(`/api/assessment-publish-tasks/${taskId}/publish`, {
    method: 'POST',
  })
  return envelope.data
}

export const stopAssessmentPublishTask = async (taskId: string) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>(`/api/assessment-publish-tasks/${taskId}/stop`, {
    method: 'POST',
  })
  return envelope.data
}

export const getAssessmentPublishMaterials = async () => {
  const envelope = await apiRequest<{
    data: {
      scale: ScaleSurvey[]
      neuropsych: NeuropsychTest[]
      reserved: Array<{ type: string; title: string; enabled: boolean }>
    }
  }>('/api/assessment-publish-tasks/materials')
  return envelope.data
}

export const getMyAssessmentPublishTasks = async () => {
  const envelope = await apiRequest<{ data: AssessmentPublishAssignee[] }>('/api/assessment-publish-tasks/my')
  return envelope.data || []
}

export const getMyAssessmentPublishTaskDetail = async (assigneeId: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/assessment-publish-tasks/my/${assigneeId}`)
  return envelope.data
}

export const startAssessmentTaskItem = async (itemRecordId: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/assessment-publish-tasks/items/${itemRecordId}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const submitAssessmentTaskModuleItem = async (itemRecordId: string, payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: any }>(`/api/assessment-publish-tasks/items/${itemRecordId}/submit`, {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const getAssessmentTaskPackageReport = async (assigneeId: string) => {
  const envelope = await apiRequest<{ data: AssessmentPackageReport }>(`/api/assessment-publish-tasks/my/${assigneeId}/report`)
  return envelope.data
}

export const getDefaultAssessmentTaskTemplate = async () => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>('/api/assessment-publish-tasks/default-template')
  return envelope.data
}

export const updateDefaultAssessmentTaskTemplate = async (payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: AssessmentPublishTask }>('/api/assessment-publish-tasks/default-template', {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const getInterventionMaterials = async () => {
  const envelope = await apiRequest<{ data: Record<string, InterventionMaterial[]> }>('/api/intervention-tasks/materials')
  return envelope.data || {}
}

export const getInterventionTemplates = async () => {
  const envelope = await apiRequest<{ data: InterventionPlanTemplate[] }>('/api/intervention-tasks/templates')
  return envelope.data || []
}

export const updateInterventionTemplate = async (templateId: string, payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: InterventionPlanTemplate }>(`/api/intervention-tasks/templates/${templateId}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const getInterventionTasks = async () => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch[] }>('/api/intervention-tasks')
  return envelope.data || []
}

export const getInterventionTask = async (batchId: string) => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch }>(`/api/intervention-tasks/${batchId}`)
  return envelope.data
}

export const createInterventionTask = async (payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch }>('/api/intervention-tasks', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const updateInterventionTask = async (batchId: string, payload: Record<string, unknown>) => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch }>(`/api/intervention-tasks/${batchId}`, {
    method: 'PUT',
    body: payload,
  })
  return envelope.data
}

export const publishInterventionTask = async (batchId: string) => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch }>(`/api/intervention-tasks/${batchId}/publish`, {
    method: 'POST',
  })
  return envelope.data
}

export const stopInterventionTask = async (batchId: string) => {
  const envelope = await apiRequest<{ data: InterventionPublishBatch }>(`/api/intervention-tasks/${batchId}/stop`, {
    method: 'POST',
  })
  return envelope.data
}

export const assignDefaultInterventionByAssessment = async (assessmentId: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/intervention-tasks/auto-assign/${assessmentId}`, {
    method: 'POST',
  })
  return envelope.data
}

export const getPatientInterventionPlan = async (userId: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/intervention-tasks/users/${userId}/plan`)
  return envelope.data
}

export const getMyInterventionTasks = async () => {
  const envelope = await apiRequest<{ data: any[] }>('/api/intervention-tasks/my')
  return envelope.data || []
}

export const getMyInterventionTodayTasks = async () => {
  const envelope = await apiRequest<{ data: InterventionTodayResponse }>('/api/intervention-tasks/my/today')
  return envelope.data
}

export const getMyInterventionPlan = async () => {
  const envelope = await apiRequest<{ data: any }>('/api/intervention-tasks/my/plan')
  return envelope.data
}

export const getMyInterventionCalendar = async (start?: string, end?: string) => {
  const envelope = await apiRequest<{ data: InterventionDailySummary[] }>('/api/intervention-tasks/my/calendar', {
    query: { ...(start ? { start } : {}), ...(end ? { end } : {}) },
  })
  return envelope.data || []
}

export const getMyInterventionCalendarDate = async (date: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/intervention-tasks/my/calendar/${date}`)
  return envelope.data
}

export const startInterventionItem = async (recordId: string) => {
  const envelope = await apiRequest<{ data: any }>(`/api/intervention-tasks/items/${recordId}/start`, {
    method: 'POST',
  })
  return envelope.data
}

export const completeInterventionItem = async (recordId: string, payload: Record<string, unknown> = {}) => {
  const envelope = await apiRequest<{ data: any }>(`/api/intervention-tasks/items/${recordId}/complete`, {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const completeTodayMoodInterventionIfAny = async (payload: Record<string, unknown> = {}) => {
  const envelope = await apiRequest<{ data: any }>('/api/intervention-tasks/my/mood/complete-today', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const createBrainInterventionReport = async (payload: BrainInterventionReportPayload) => {
  const envelope = await apiRequest<{ data: BrainInterventionReport }>('/api/brain-intervention-reports', {
    method: 'POST',
    body: payload,
  })
  return envelope.data
}

export const getMyBrainInterventionReports = async () => {
  const envelope = await apiRequest<{ data: BrainInterventionReport[] }>('/api/brain-intervention-reports/my')
  return envelope.data || []
}

export const getMyBrainInterventionReport = async (reportId: string) => {
  const envelope = await apiRequest<{ data: BrainInterventionReport }>(`/api/brain-intervention-reports/my/${reportId}`)
  return envelope.data
}

export const getBrainInterventionReports = async (filters: Record<string, string | number | undefined> = {}) => {
  const envelope = await apiRequest<{ data: BrainInterventionReport[] }>('/api/brain-intervention-reports', {
    query: filters,
  })
  return envelope.data || []
}

export const getBrainInterventionReport = async (reportId: string) => {
  const envelope = await apiRequest<{ data: BrainInterventionReport }>(`/api/brain-intervention-reports/${reportId}`)
  return envelope.data
}
