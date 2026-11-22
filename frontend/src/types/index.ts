export type UserRole = 'user' | 'doctor' | 'admin' | 'super_admin'

export type MoodLevel = 'very_good' | 'good' | 'neutral' | 'bad' | 'very_bad'
export type EmotionLevel = MoodLevel

export interface QuickAction {
  title: string
  color: string
  icon: string
  path: string
  query?: Record<string, string>
}

export interface FeatureCard {
  title: string
  subtitle: string
  description: string
  icon: string
  path: string
  gradient: string
}

export interface MeditationTrack {
  id: string
  title: string
  category: 'sleep' | 'relax' | 'focus'
  duration: string
  cover: string
  emoji: string
  audio: string
  description: string
}

export interface VideoContent {
  id: string
  title: string
  duration: string
  cover: string
  video: string
  summary: string
}

export interface AssessmentSectionResult {
  score: number
  label: string
  summary: string
}

export interface AssessmentRecord {
  id: string
  createdAt: string
  scale: AssessmentSectionResult
  voice: AssessmentSectionResult
  expression: AssessmentSectionResult
  overall: AssessmentSectionResult
  report?: Record<string, any>
}

export interface DiaryEntry {
  id: string
  date: string
  mood: MoodLevel
  content: string
  triggers: string[]
  images: string[]
  aiAnalysis?: {
    analysis?: string
    summary?: string
    timestamp?: string
  } | null
  createdAt?: string
}

export interface PrivacySetting {
  id: string
  title: string
  description: string
  enabled: boolean
}

export interface SubscriptionPlan {
  id: string
  name: string
  price: string
  description: string
  perks: string[]
  recommended?: boolean
}

export interface HealingTask {
  id: string
  title: string
  frequency: string
  progress: number
  streak: number
}

export interface DoctorProfile {
  id: string
  name: string
  hospital: string
  specialty: string
  availability: string
  note: string
}

export interface SmartBandMetric {
  label: string
  value: string
  trend: string
}

export interface PatientRecord {
  id: string
  name: string
  risk: 'low' | 'medium' | 'high'
  mood: string
  lastAssessment: string
  adherence: number
}

export interface AlertItem {
  id: string
  level: 'low' | 'medium' | 'high'
  title: string
  patient: string
  time: string
  description: string
  resolved: boolean
}

export interface AppProfile {
  phoneNumber: string
  username: string
}

export interface KnowledgeArticle {
  id: string
  title: string
  category: string
  description: string
  tags: string[]
  content: string
}

export interface Profile {
  id: string
  username: string
  email?: string | null
  phone?: string | null
  wechat?: string | null
  role: UserRole
  department_id?: string | null
  department_name?: string | null
  department_status?: string | null
  avatar_url?: string | null
  full_name?: string | null
  gender?: string | null
  birth_date?: string | null
  bio?: string | null
  background_url?: string | null
  selected_background?: string | null
  created_at: string
  updated_at: string
}

export interface Department {
  id: string
  name: string
  description?: string | null
  status: 'active' | 'inactive'
  user_count?: number
  created_at?: string
  updated_at?: string
}

export interface EmotionDiary {
  id: string
  user_id: string
  diary_date: string
  emotion_level: EmotionLevel
  title?: string | null
  content?: string | null
  tags?: string[] | null
  image_urls?: string[] | null
  voice_url?: string | null
  ai_analysis?: unknown
  created_at: string
  updated_at: string
}

export interface Assessment {
  id: string
  user_id: string
  assessment_type: string
  conversation_history: unknown[]
  text_input?: string | null
  voice_input_url?: string | null
  image_input_url?: string | null
  video_input_url?: string | null
  ai_analysis?: unknown
  risk_level?: number | null
  score?: number | null
  report?: any
  created_at: string
  updated_at: string
}

export interface WearableData {
  id: string
  user_id: string
  record_date: string
  heart_rate?: number | null
  sleep_hours?: number | null
  sleep_quality?: number | null
  steps?: number | null
  calories?: number | null
  stress_level?: number | null
  blood_oxygen?: number | null
  temperature?: number | null
  data_json?: unknown
  created_at: string
}

export type TimeRange = 'day' | 'week' | 'month'

export type BandConnectionStatus = 'disconnected' | 'scanning' | 'connecting' | 'connected' | 'connection_failed'

export interface SmartBandDevice {
  id: string
  name: string
  manufacturer: string
  model: string
  rssi?: number
}

export interface HealingContent {
  id: string
  title: string
  description?: string | null
  category: string
  content_type: string
  content_url?: string | null
  duration?: number | null
  thumbnail_url?: string | null
  author?: string | null
  tags?: string[] | null
  is_active: boolean
  view_count: number
  like_count?: number | null
  created_at: string
  updated_at: string
}

export interface UserHealingRecord {
  id: string
  user_id: string
  healing_content_id: string
  duration_seconds?: number | null
  completed: boolean
  created_at: string
}

export interface CommunityPost {
  id: string
  user_id: string
  anonymous_name: string
  anonymous_nickname?: string | null
  title: string
  content: string
  category_id?: string | null
  tags?: string[] | null
  like_count: number
  comment_count: number
  is_pinned: boolean
  is_hidden: boolean
  is_recovery_story?: boolean | null
  is_featured?: boolean | null
  post_categories?: unknown
  created_at: string
  updated_at: string
}

export interface CommunityComment {
  id: string
  post_id: string
  user_id: string
  anonymous_name: string
  content: string
  like_count: number
  created_at: string
}

export interface DoctorPatient {
  id: string
  doctor_id: string
  patient_id: string
  status: string
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface RiskAlert {
  id: string
  patient_id: string
  alert_type: string
  risk_level: number
  description: string
  data_source?: string | null
  source_id?: string | null
  is_handled: boolean
  handled_by?: string | null
  handled_at?: string | null
  notes?: string | null
  created_at: string
}

export type ScaleAssessmentCategory = 'scale' | 'neuropsych'
export type ScaleWarningLevel = 'none' | 'low' | 'middle' | 'high'
export type ScaleCalcStatus = 'none' | 'waiting' | 'done' | 'error'
export type ScaleRecordStatus = 'pending' | 'in_progress' | 'completed' | 'expired' | 'cancelled'
export type ScaleQuestionType = 'radio' | 'checkbox' | 'text'

export interface ScaleOption {
  id: string
  question_id?: string
  option_no: string
  label: string
  value: number
  order_no: number
  media_url?: string | null
}

export interface ScaleQuestion {
  id: string
  survey_id?: string
  question_type: ScaleQuestionType
  stem: string
  media_url?: string | null
  order_no: number
  required: boolean
  options?: ScaleOption[]
}

export interface ScaleResultDefinition {
  id: string
  dimension_id?: string
  condition_expression: string
  conclusion?: string | null
  suggestion?: string | null
  warning_level: ScaleWarningLevel
  order_no: number
}

export interface ScaleDimension {
  id: string
  survey_id?: string
  name: string
  code?: string | null
  num: number
  raw_score_formula: string
  standard_score_formula?: string | null
  show_in_full_report?: boolean
  show_in_user_report?: boolean
  show_chart?: boolean
  result_definitions?: ScaleResultDefinition[]
}

export interface ScaleSurvey {
  id: string
  code: string
  title: string
  description?: string | null
  cover_url?: string | null
  survey_type?: string | null
  status: 'draft' | 'published' | 'stopped'
  self_test_enabled: boolean
  survey_json?: any
  version: number
  created_by?: string | null
  published_at?: string | null
  created_at?: string
  updated_at?: string
  question_count?: number
  distribution_count?: number
  questions?: ScaleQuestion[]
  dimensions?: ScaleDimension[]
}

export interface HuaxinyunScaleImportItem {
  source_id?: string
  code: string
  title: string
  question_count: number
  dimension_count: number
  result_count: number
  can_import: boolean
  can_publish: boolean
  action?: string
  survey_id?: string
  issues: string[]
  warnings: string[]
}

export interface HuaxinyunScaleImportResult {
  dry_run: boolean
  publish: boolean
  overwrite: boolean
  skip_invalid: boolean
  total: number
  importable: number
  publishable: number
  imported: number
  updated: number
  skipped: number
  failed: number
  items: HuaxinyunScaleImportItem[]
}

export interface ScaleDistributionPlan {
  id: string
  title: string
  assessment_category: ScaleAssessmentCategory
  survey_ids?: string[]
  recipient_type: 'users' | 'groups'
  recipient_scope?: any
  cover_url?: string | null
  start_at?: string | null
  end_at?: string | null
  status: 'draft' | 'active' | 'stopped'
  created_by?: string | null
  created_at: string
  updated_at: string
  record_count?: number
  completed_count?: number
}

export interface ScaleRecordDimension {
  id?: string
  record_id?: string
  dimension_id?: string
  dimension_name?: string
  name?: string
  dimension_code?: string | null
  raw_score?: number
  rawScore?: number
  standard_score?: number
  standardScore?: number
  conclusion?: string | null
  suggestion?: string | null
  warning_level?: ScaleWarningLevel
  warningLevel?: ScaleWarningLevel
}

export interface ScaleAnswer {
  id?: string
  record_id?: string
  question_id: string
  question_type: ScaleQuestionType
  my_answer: string
  answer_text?: string | null
  option_no?: string | null
  score?: number
}

export interface ScaleDistributionRecord {
  id: string
  plan_id?: string | null
  survey_id: string
  user_id: string
  assessment_category: ScaleAssessmentCategory
  source_type?: 'assigned' | 'self'
  status: ScaleRecordStatus
  calc_status: ScaleCalcStatus
  calc_error?: string | null
  sent_at: string
  started_at?: string | null
  completed_at?: string | null
  answer_duration_sec?: number | null
  answers_json?: any
  total_score?: number | null
  warning_level: ScaleWarningLevel
  report?: any
  assessment_id?: string | null
  plan_title?: string
  start_at?: string | null
  end_at?: string | null
  survey_title?: string
  survey_code?: string
  patient_name?: string
  patient_username?: string
  survey?: ScaleSurvey
  answers?: ScaleAnswer[]
  dimensions?: ScaleRecordDimension[]
}

export type NeuropsychWarningLevel = ScaleWarningLevel
export type NeuropsychRecordStatus = ScaleRecordStatus
export type NeuropsychCalcStatus = ScaleCalcStatus
export type AssessmentPublishItemType = 'scale' | 'neuropsych' | 'dialogue_scale' | 'voice' | 'expression' | 'multimodal_baseline'

export type NeuropsychMobileControlTone = 'primary' | 'secondary' | 'success' | 'warning' | 'danger'
export type NeuropsychMobileControlActionType = 'keypress' | 'click' | 'command'

export interface NeuropsychMobileControlAction {
  id: string
  label: string
  helper?: string
  icon?: string
  tone?: NeuropsychMobileControlTone
  type: NeuropsychMobileControlActionType
  key?: string
  code?: string
  keyCode?: number
  selectors?: string[]
  command?: 'advance' | 'clickFirstAvailableCard'
}

export interface NeuropsychTestConfig {
  engine?: string
  source?: string
  mode?: string
  mobileControls?: NeuropsychMobileControlAction[]
  [key: string]: any
}

export interface NeuropsychTest {
  id: string
  code: 'go-nogo' | 'columbia-card-task-hot' | 'discount-titrate' | 'stroop' | string
  title: string
  description?: string | null
  dimension?: string | null
  clinical_meaning?: string | null
  estimated_minutes?: number | null
  source_path?: string | null
  runner_type?: string
  status: 'active' | 'stopped'
  self_test_enabled: boolean
  config_json?: NeuropsychTestConfig | null
  metric_schema_json?: any
  scoring_version?: number
  record_count?: number
  completed_count?: number
  created_at?: string
  updated_at?: string
}

export interface NeuropsychFeedbackCard {
  title: string
  subtitle?: string
  level: NeuropsychWarningLevel
  primaryValue?: string
  items?: Array<{ label: string; value: string | number; trend?: string }>
  conclusion?: string
  suggestion?: string
}

export interface NeuropsychReport {
  recordId?: string
  testId?: string
  testCode?: string
  testTitle?: string
  completedAt?: string
  summary?: string
  warningLevel?: NeuropsychWarningLevel
  quality?: { valid?: boolean; message?: string }
  metrics?: Record<string, any>
  feedbackCards?: NeuropsychFeedbackCard[]
  feedback?: Record<string, any>
  sections?: Array<{ title: string; level: NeuropsychWarningLevel; conclusion?: string; suggestion?: string }>
  rawDataPreview?: any[]
}

export interface NeuropsychRecord {
  id: string
  test_id: string
  user_id: string
  source_type: 'assigned' | 'self'
  publish_item_record_id?: string | null
  status: NeuropsychRecordStatus
  calc_status: NeuropsychCalcStatus
  calc_error?: string | null
  started_at?: string | null
  completed_at?: string | null
  duration_ms?: number | null
  raw_data_json?: any
  metrics_json?: Record<string, any> | null
  report?: NeuropsychReport | null
  warning_level: NeuropsychWarningLevel
  assessment_id?: string | null
  test_code?: string
  test_title?: string
  test_description?: string | null
  dimension?: string | null
  clinical_meaning?: string | null
  estimated_minutes?: number | null
  source_path?: string | null
  config_json?: NeuropsychTestConfig | null
  batch_title?: string | null
  patient_name?: string | null
  patient_username?: string | null
  created_at?: string
  updated_at?: string
}

export interface AssessmentPublishItem {
  id?: string
  batch_id?: string
  item_type: AssessmentPublishItemType
  target_id?: string | null
  title: string
  required: boolean
  order_no?: number
  config_json?: any
  status?: 'enabled' | 'disabled'
}

export interface AssessmentPublishItemRecord {
  id: string
  assignee_id: string
  batch_id: string
  item_id: string
  user_id: string
  item_type: AssessmentPublishItemType
  status: NeuropsychRecordStatus | 'unsupported'
  result_ref_table?: string | null
  result_ref_id?: string | null
  report?: any
  warning_level?: ScaleWarningLevel
  title?: string
  required?: boolean
  order_no?: number
  target_id?: string | null
  config_json?: any
  started_at?: string | null
  completed_at?: string | null
  result?: any
}

export interface AssessmentPublishAssignee {
  id: string
  batch_id: string
  user_id: string
  status: NeuropsychRecordStatus
  patient_name?: string | null
  patient_username?: string | null
  batch_title?: string
  batch_description?: string | null
  start_at?: string | null
  end_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  items?: AssessmentPublishItemRecord[]
  package_report?: Assessment | null
}

export interface AssessmentPublishTask {
  id: string
  batch_type?: 'manual' | 'auto_default'
  template_code?: string | null
  auto_assign_enabled?: boolean
  title: string
  description?: string | null
  status: 'draft' | 'active' | 'stopped'
  start_at?: string | null
  end_at?: string | null
  recipient_type?: 'users' | 'groups'
  recipient_scope?: any
  created_by?: string | null
  published_at?: string | null
  created_at?: string
  updated_at?: string
  item_count?: number
  assignee_count?: number
  completed_count?: number
  items?: AssessmentPublishItem[]
  assignees?: AssessmentPublishAssignee[]
}

export interface AssessmentTaskModuleRecord {
  id: string
  item_record_id: string
  user_id: string
  module_type: Extract<AssessmentPublishItemType, 'dialogue_scale' | 'voice' | 'expression' | 'multimodal_baseline'>
  status: NeuropsychRecordStatus
  raw_data_json?: any
  metrics_json?: any
  report?: any
  warning_level: ScaleWarningLevel
  started_at?: string | null
  completed_at?: string | null
  created_at?: string
  updated_at?: string
}

export interface AssessmentPackageReport {
  assessmentId: string
  report: {
    packageData?: any
    sections?: any[]
    scaleData?: any
    neuropsychData?: any
    dialogueData?: any
    voiceData?: any
    expressionData?: any
    overall?: any
    weights?: any
    advice?: string
    fusionAi?: any
  }
}

export type InterventionCategory = 'meditation' | 'mood' | 'game' | 'knowledge' | 'brain_intervention'
export type InterventionStatus = 'pending' | 'in_progress' | 'completed' | 'expired' | 'cancelled'
export type InterventionRiskLevel = 'low' | 'middle' | 'high'
export type InterventionFrequencyType = 'daily' | 'weekly' | 'once' | 'plan_total'
export type InterventionCompletionMode = 'countdown' | 'diary_once' | 'media_end'

export type BrainInterventionReportStatus = 'completed' | 'interrupted' | 'invalid'
export type BrainInterventionTaskType = 'neurofeedback' | 'ssvep' | 'p300' | 'smr' | 'relaxation' | 'attention_training' | 'meditation_biosignal_monitor'

export interface BrainInterventionReport {
  id: string
  user_id: string
  user_name?: string | null
  doctor_id?: string | null
  report_type: 'brain_intervention'
  task_type: BrainInterventionTaskType
  task_name: string
  protocol_key?: string | null
  started_at: string
  ended_at?: string | null
  duration_sec: number
  status: BrainInterventionReportStatus
  main_score?: number | null
  avg_score?: number | null
  max_score?: number | null
  stable_duration_sec?: number | null
  signal_quality_avg?: number | null
  artifact_ratio?: number | null
  summary?: string | null
  suggestion?: string | null
  metrics_json?: Record<string, any> | null
  curve_json?: Record<string, any> | null
  config_json?: Record<string, any> | null
  patient_username?: string | null
  patient_full_name?: string | null
  patient_department_id?: string | null
  patient_department_name?: string | null
  created_at?: string
  updated_at?: string
}

export interface BrainInterventionReportPayload {
  user_id?: string
  report_type?: 'brain_intervention'
  task_type: BrainInterventionTaskType
  task_name: string
  protocol_key?: string
  started_at: string
  ended_at: string
  duration_sec: number
  status: BrainInterventionReportStatus
  main_score?: number | null
  avg_score?: number | null
  max_score?: number | null
  stable_duration_sec?: number | null
  signal_quality_avg?: number | null
  artifact_ratio?: number | null
  summary?: string | null
  suggestion?: string | null
  metrics_json?: Record<string, any>
  curve_json?: Record<string, any>
  config_json?: Record<string, any>
}

export interface InterventionMaterial {
  id: string
  code: string
  title: string
  description?: string | null
  category: InterventionCategory
  subtype?: string | null
  target_ref_table?: string | null
  target_ref_id?: string | null
  route_path: string
  duration_sec: number
  completion_mode: InterventionCompletionMode
  tags?: string[] | null
  config_json?: any
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface InterventionPlanTemplateItem {
  id?: string
  template_id?: string
  material_id: string
  title: string
  frequency_type: InterventionFrequencyType
  required_count: number
  duration_sec: number
  order_no?: number
  required: boolean
  config_json?: any
  category?: InterventionCategory
  subtype?: string | null
  route_path?: string
  completion_mode?: InterventionCompletionMode
}

export interface InterventionPlanTemplate {
  id: string
  code: string
  title: string
  risk_level: InterventionRiskLevel
  description?: string | null
  duration_days: number
  daily_required_count: number
  auto_assign_enabled: boolean
  status: 'draft' | 'active' | 'stopped'
  items?: InterventionPlanTemplateItem[]
}

export interface InterventionPublishItem {
  id?: string
  batch_id?: string
  material_id: string
  item_type?: InterventionCategory
  subtype?: string | null
  title: string
  route_path?: string
  required: boolean
  frequency_type: InterventionFrequencyType
  required_count: number
  duration_sec: number
  completion_mode?: InterventionCompletionMode
  order_no?: number
  config_json?: any
  status?: 'enabled' | 'disabled'
}

export interface InterventionPublishAssignee {
  id: string
  batch_id: string
  user_id: string
  source_assessment_id?: string | null
  status: InterventionStatus
  start_date: string
  end_date: string
  completed_days: number
  total_completed_count: number
  last_completed_at?: string | null
  batch_title?: string
  batch_description?: string | null
  risk_level?: InterventionRiskLevel | null
  duration_days?: number
  daily_required_count?: number
  items?: InterventionPublishItem[]
  patient_name?: string | null
  patient_username?: string | null
}

export interface InterventionPublishBatch {
  id: string
  batch_type: 'manual' | 'auto_after_screening' | 'auto_baseline'
  template_id?: string | null
  source_assessment_id?: string | null
  title: string
  description?: string | null
  risk_level?: InterventionRiskLevel | null
  duration_days: number
  daily_required_count: number
  status: 'draft' | 'active' | 'stopped' | 'completed'
  start_date?: string | null
  end_date?: string | null
  recipient_scope?: any
  created_by?: string | null
  published_at?: string | null
  created_at?: string
  updated_at?: string
  item_count?: number
  assignee_count?: number
  finished_count?: number
  average_completed_count?: number
  items?: InterventionPublishItem[]
  assignees?: InterventionPublishAssignee[]
}

export interface InterventionTodayTask {
  id: string
  record_ids?: string[]
  assignee_id: string
  batch_id: string
  item_id: string
  material_id: string
  user_id: string
  plan_date: string
  status: InterventionStatus
  title: string
  item_type: InterventionCategory
  route_path: string
  navigation_path: string
  frequency_type: InterventionFrequencyType
  required_count: number
  duration_sec: number
  completion_mode: InterventionCompletionMode
  required: boolean
  batch_title?: string
  risk_level?: InterventionRiskLevel | null
  material_description?: string | null
  subtype?: string | null
  target_ref_table?: string | null
  target_ref_id?: string | null
  source_ref_id?: string | null
}

export interface InterventionDailySummary {
  id: string
  assignee_id: string
  user_id: string
  summary_date: string
  completed_count: number
  required_count: number
  mood_level?: string | null
  summary_text?: string | null
  details_json?: any
  created_at?: string
  updated_at?: string
}

export interface InterventionTodayResponse {
  date: string
  tasks: InterventionTodayTask[]
  summary: {
    total: number
    completed: number
    pending: number
    itemTotal?: number
    itemCompleted?: number
    requiredTotal?: number
    optionalTotal?: number
    planTargetTotal?: number
    planCompletedTotal?: number
  }
}

export interface KnowledgeBase {
  id: string
  title: string
  content: string
  category: string
  tags?: string[] | null
  content_type?: 'text' | 'document' | null
  file_url?: string | null
  file_name?: string | null
  file_size?: number | null
  file_mime_type?: string | null
  is_active: boolean
  created_by?: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface MultimodalContent {
  type: 'text' | 'image_url'
  text?: string
  image_url?: {
    url: string
  }
}

export interface MultimodalMessage {
  role: 'system' | 'user' | 'assistant'
  content: MultimodalContent[]
}
