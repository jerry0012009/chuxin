import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import DashboardPage from '@/pages/doctor/DashboardPage.vue'
import AlertsPage from '@/pages/doctor/AlertsPage.vue'
import AssessmentPage from '@/pages/user/AssessmentPage.vue'
import HomePage from '@/pages/user/HomePage.vue'

const api = vi.hoisted(() => ({
  getMyAssessmentPublishTasks: vi.fn(),
  getMyInterventionTodayTasks: vi.fn(),
  getMyScaleRecords: vi.fn(),
  getAllProfiles: vi.fn(),
  getRiskAlerts: vi.fn(),
  getAllAssessments: vi.fn(),
  getAllEmotionDiaries: vi.fn(),
  handleRiskAlert: vi.fn(),
  getKnowledgeBase: vi.fn(),
  chatCompletion: vi.fn(),
  multimodalAnalysis: vi.fn(),
  multimodalFusion: vi.fn(),
  speechRecognition: vi.fn(),
  submitAssessmentTaskModuleItem: vi.fn(),
}))

vi.mock('@/db/api', () => api)
vi.mock('vue-router', async (importOriginal) => ({
  ...await importOriginal<typeof import('vue-router')>(),
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn() }),
}))
vi.mock('@/composables/useAppState', () => ({
  useAppState: () => ({ state: { assessments: [], currentAccountId: 'fixture' }, addAssessment: vi.fn(), refreshAssessments: vi.fn() }),
}))
vi.mock('@/composables/useAuthSession', () => ({
  useAuthSession: () => ({ state: { user: { id: 'fixture' }, profile: { full_name: '版式测试员' } } }),
}))

const global = { stubs: { RouterLink: RouterLinkStub } }
const date = '2026-11-24T12:00:00Z'
const alert = (id: string, risk: number, when = date) => ({
  id, patient_id: 'fixture', risk_level: risk, alert_type: '测试分类', description: id, created_at: when,
})

beforeEach(() => {
  vi.resetAllMocks()
  localStorage.clear()
  Object.values(api).forEach((fn) => fn.mockResolvedValue([]))
  api.getMyInterventionTodayTasks.mockResolvedValue({ tasks: [], summary: { total: 0, completed: 0 } })
})

describe('editorial workspace', () => {
  it('binds the main scene to required progress and keeps the real task and report routes', async () => {
    const title = '高原身心状态综合测评'.repeat(8)
    api.getMyAssessmentPublishTasks.mockResolvedValue([{
      id: 'current', status: 'in_progress', batch_title: title, items: [
        { required: true, status: 'completed', item_type: 'scale' },
        { required: false, status: 'completed', item_type: 'voice' },
        { required: true, status: 'pending', title: '神经心理测验', item_type: 'neuropsych' },
      ],
    }])
    api.getMyScaleRecords.mockResolvedValue([
      { id: 'report', status: 'completed', calc_status: 'done', survey_title: '验收量表', completed_at: date },
      { id: 'waiting', status: 'completed', calc_status: 'waiting', survey_title: '未评分报告', completed_at: date },
    ])
    const wrapper = mount(HomePage, { global })
    await flushPromises()
    const scene = wrapper.get('[data-testid="work-current"]')
    expect(scene.get('h2').text()).toBe(title)
    expect(scene.get('progress').attributes('value')).toBe('50')
    expect(scene.text()).toContain('神经心理测验')
    expect(wrapper.findAllComponents(RouterLinkStub).find((link) => link.attributes('data-testid') === 'work-current-link')?.props('to')).toBe('/assessment-tasks/current')
    expect(wrapper.get('[data-testid="work-records"] ul').text()).toContain('验收量表')
    expect(wrapper.findAllComponents(RouterLinkStub).map((link) => link.props('to'))).toContainEqual({ path: '/scale-assessment', query: { recordId: 'report' } })
    expect(wrapper.text()).not.toContain('未评分报告')
    wrapper.unmount()
  })

  it('distinguishes failed requests from empty states and retries', async () => {
    api.getMyAssessmentPublishTasks.mockRejectedValueOnce(new Error('fixture unavailable'))
    const wrapper = mount(HomePage, { global })
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('测评任务加载失败')
    expect(wrapper.text()).not.toContain('暂无待办测评')
    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(wrapper.get('#work-current-heading').text()).toBe('暂无待办测评')
    expect(wrapper.text()).toContain('今日暂无干预任务')
    wrapper.unmount()
  })

  it('puts risk ahead of recency and preserves zero scores and missing mood data', async () => {
    api.getAllProfiles.mockResolvedValue([{ id: 'fixture', role: 'user', full_name: '版式测试员' }])
    api.getRiskAlerts.mockResolvedValue([alert('较新中风险', 6), alert('较早高风险', 9, '2026-11-23T12:00:00Z')])
    api.getAllAssessments.mockResolvedValue([{ id: 'score', user_id: 'fixture', score: 0, assessment_type: 'scale', created_at: date }])
    const wrapper = mount(DashboardPage, { global })
    await flushPromises()
    expect(wrapper.findAll('.dashboard-alerts li').map((row) => row.get('p').text())).toEqual(['较早高风险', '较新中风险'])
    expect(wrapper.get('.dashboard-score').text()).toMatch(/0$/)
    expect(wrapper.text()).toContain('近 7 日暂无情绪日记')
    wrapper.unmount()
  })

  it('keeps the evaluation action, session, report gate and history focus across module switches', async () => {
    const wrapper = mount(AssessmentPage, { attachTo: document.body })
    await flushPromises()
    const history = wrapper.get('[data-testid="scale-history-trigger"]')
    await history.trigger('click')
    await flushPromises()
    const close = wrapper.get('[data-testid="scale-history-close"]')
    expect(document.activeElement).toBe(close.element)
    await close.trigger('keydown', { key: 'Escape' })
    await flushPromises()
    expect(document.activeElement).toBe(history.element)
    const report = wrapper.get<HTMLButtonElement>('[data-testid="generate-fusion-report"]')
    expect(report.element.disabled).toBe(true)
    await wrapper.get('[data-testid="start-scale-assessment"]').trigger('click')
    await flushPromises()
    const answer = wrapper.get('[data-testid="scale-dialogue-input"]')
    await wrapper.get('[data-testid="assessment-step-voice"]').trigger('click')
    expect(wrapper.get('#assessment-panel-scale').isVisible()).toBe(false)
    await wrapper.get('[data-testid="assessment-step-scale"]').trigger('click')
    expect(answer.isVisible()).toBe(true)
    expect(report.element.disabled).toBe(true)
    wrapper.unmount()
  })

  it('keeps the alert handling API, notes, and keyboard focus', async () => {
    api.getRiskAlerts.mockImplementation(async (handled: boolean) => handled ? [] : [alert('待处理样例', 8)])
    const wrapper = mount(AlertsPage, { attachTo: document.body })
    await flushPromises()
    const trigger = wrapper.get('[data-testid="alert-handle-trigger"]')
    await trigger.trigger('click')
    const notes = wrapper.get('[data-testid="alert-notes-input"]')
    expect(document.activeElement).toBe(notes.element)
    await notes.trigger('keydown', { key: 'Escape' })
    expect(document.activeElement).toBe(trigger.element)
    await trigger.trigger('click')
    await wrapper.get('[data-testid="alert-notes-input"]').setValue('  测试备注  ')
    await wrapper.get('[data-testid="alert-confirm-handle"]').trigger('click')
    await flushPromises()
    expect(api.handleRiskAlert).toHaveBeenCalledWith('待处理样例', 'fixture', '测试备注')
    expect(document.activeElement).toBe(wrapper.get('[data-testid="alerts-tab-pending"]').element)
    wrapper.unmount()
  })
})
