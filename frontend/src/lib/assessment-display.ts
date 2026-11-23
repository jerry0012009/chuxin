import type { Assessment, AssessmentPublishItemRecord } from '@/types'

const itemNames = {
  scale: '量表测评', neuropsych: '神经心理测验', dialogue_scale: '对话式心理健康评估',
  voice: '语音识别', expression: '表情评估', multimodal_baseline: '多模态基线',
}

export const canOpenAssessmentItem = (item: AssessmentPublishItemRecord) => ['pending', 'in_progress'].includes(item.status)

export function nextAssessmentItem(items: AssessmentPublishItemRecord[]) {
  const required = items.filter((item) => item.required !== false)
  return required.find((item) => item.status === 'in_progress') || required.find(canOpenAssessmentItem) || items.find(canOpenAssessmentItem)
}

export const assessmentItemName = (item: AssessmentPublishItemRecord) => item.title || itemNames[item.item_type] || '测评项目'

const statuses: Record<string, string> = {
  draft: '草稿', published: '已发布', archived: '已归档', active: '进行中', stopped: '已停止',
  pending: '待完成', in_progress: '进行中', completed: '已完成', expired: '已过期', cancelled: '已取消',
  none: '未评分', waiting: '待评分', done: '已评分', error: '评分失败',
}

export const assessmentStatusLabel = (status?: string | null) => (status && statuses[status]) || '状态未记录'

export function assessmentTypeLabel(item: Pick<Assessment, 'assessment_type' | 'report'>) {
  const type = (item.assessment_type || '').toLowerCase()
  if (type.includes('package')) return '测评任务综合报告'
  if (type.includes('fusion') || type.includes('multimodal')) return '多模态综合评估'
  if (type.includes('htp')) return '房树人评估'
  if (type.includes('neuropsych')) return '神经心理测评'
  if (type.includes('voice') || item.report?.voiceData) return '语音情绪评估'
  if (type.includes('expression') || type.includes('face') || item.report?.expressionData) return '表情评估'
  if (type.includes('scale') || item.report?.scaleData) return '量表测评'
  return '其他评估'
}
