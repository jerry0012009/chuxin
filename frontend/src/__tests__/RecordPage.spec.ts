import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const appStateMock = vi.hoisted(() => ({
  state: {
    currentAccountId: 'user-42',
    currentAccountRole: 'user',
    currentAccountCreatedAt: '',
    profile: { phoneNumber: '13800000000', username: '记录用户' },
    diaries: [
      {
        id: 'diary-21',
        date: '2026-05-27',
        mood: 'good',
        content: '后端页面记录',
        triggers: ['运动'],
        images: [],
        createdAt: '2026-05-27T08:00:00Z',
      },
    ],
    assessments: [],
    knowledge: [],
    privacy: [],
    alerts: [],
    selectedDoctorId: '',
  },
  sortedDiaries: {
    value: [
      {
        id: 'diary-21',
        date: '2026-05-27',
        mood: 'good',
        content: '后端页面记录',
        triggers: ['运动'],
        images: [],
        createdAt: '2026-05-27T08:00:00Z',
      },
    ],
  },
  loadEmotionRecords: vi.fn(async () => {}),
  createEmotionRecord: vi.fn(async () => ({
    id: 'diary-22',
    date: '2026-05-29',
    mood: 'neutral',
    content: '新增页面记录',
    triggers: [],
    images: [],
    createdAt: '2026-05-29T09:00:00Z',
  })),
}))

const dbApiMock = vi.hoisted(() => ({
  completeInterventionItem: vi.fn(async () => ({ completed: true })),
  completeTodayMoodInterventionIfAny: vi.fn(async () => ({ completed: true })),
  speechRecognition: vi.fn(async () => ({ text: '' })),
  updateEmotionDiary: vi.fn(async () => ({})),
}))

vi.mock('@/composables/useAppState', () => ({
  useAppState: () => appStateMock,
}))

vi.mock('@/db/api', () => dbApiMock)

describe('RecordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.assign(appStateMock.state, {
      currentAccountId: 'user-42',
      diaries: [
        {
          id: 'diary-21',
          date: '2026-05-27',
          mood: 'good',
          content: '后端页面记录',
          triggers: ['运动'],
          images: [],
          createdAt: '2026-05-27T08:00:00Z',
        },
      ],
    })
  })

  it('loads current emotion diaries through useAppState when the page opens', async () => {
    const RecordPage = (await import('@/pages/user/RecordPage.vue')).default
    const wrapper = mount(RecordPage)
    await flushPromises()

    expect(appStateMock.loadEmotionRecords).toHaveBeenCalled()
    expect(wrapper.text()).toContain('情绪日记')
    expect(wrapper.text()).toContain('保存记录')
  })

  it('saves a new record through the current app-state contract', async () => {
    const RecordPage = (await import('@/pages/user/RecordPage.vue')).default
    const wrapper = mount(RecordPage)
    await flushPromises()
    await wrapper.get('textarea').setValue('新增页面记录')
    await wrapper.get('[data-testid="save-emotion-record"]').trigger('click')
    await flushPromises()

    expect(appStateMock.createEmotionRecord).toHaveBeenCalledWith({
      date: expect.any(String),
      mood: 'neutral',
      content: '新增页面记录',
      triggers: [],
      images: [],
    })
    expect(dbApiMock.completeTodayMoodInterventionIfAny).toHaveBeenCalledWith({
      source_ref_table: 'emotion_diaries',
      source_ref_id: 'diary-22',
      duration_seconds: 0,
      summary_json: {
        mood: 'neutral',
        triggerCount: 0,
        contentLength: 6,
      },
    })
    expect(wrapper.text()).toContain('记录已保存')
  })
})
