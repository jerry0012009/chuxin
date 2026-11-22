import { beforeEach, describe, expect, it, vi } from 'vitest'

const authMock = vi.hoisted(() => ({
  state: {
    initialized: true,
    user: {
      id: 'user-42',
      user_metadata: { role: 'user' },
    },
    profile: {
      id: 'user-42',
      username: '记录用户',
      phone: '13800000000',
      role: 'user',
      created_at: '2026-05-25T11:00:00Z',
      updated_at: '2026-05-25T11:00:00Z',
    },
  },
  ensureInitialized: vi.fn(async () => {}),
}))

const dbMock = vi.hoisted(() => ({
  createEmotionDiary: vi.fn(),
  createRiskAlert: vi.fn(),
  getAssessments: vi.fn(),
  getEmotionDiaries: vi.fn(),
  getProfile: vi.fn(),
  syncReport: vi.fn(),
  updateEmotionDiary: vi.fn(),
}))

vi.mock('@/composables/useAuthSession', () => ({
  useAuthSession: () => authMock,
}))

vi.mock('@/db/api', () => dbMock)

const resetDbMocks = () => {
  dbMock.getProfile.mockResolvedValue({
    id: 'user-42',
    username: '数据库用户',
    phone: '13900000007',
    role: 'user',
    created_at: '2026-05-25T11:00:00Z',
    updated_at: '2026-05-25T11:00:00Z',
  })
  dbMock.getEmotionDiaries.mockResolvedValue([
    {
      id: 'diary-15',
      user_id: 'user-42',
      diary_date: '2026-05-27',
      emotion_level: 'good',
      content: '后端记录',
      tags: ['运动'],
      image_urls: [],
      ai_analysis: null,
      created_at: '2026-05-27T07:30:00Z',
      updated_at: '2026-05-27T07:30:00Z',
    },
  ])
  dbMock.getAssessments.mockResolvedValue([])
  dbMock.createEmotionDiary.mockResolvedValue({
    id: 'diary-16',
    user_id: 'user-42',
    diary_date: '2026-05-28',
    emotion_level: 'bad',
    content: '晚上有些焦虑',
    tags: ['工作压力'],
    image_urls: [],
    ai_analysis: null,
    created_at: '2026-05-28T12:00:00Z',
    updated_at: '2026-05-28T12:00:00Z',
  })
  dbMock.updateEmotionDiary.mockResolvedValue({
    id: 'diary-15',
    user_id: 'user-42',
    diary_date: '2026-05-27',
    emotion_level: 'neutral',
    content: '更新后的记录',
    tags: ['运动'],
    image_urls: [],
    ai_analysis: null,
    created_at: '2026-05-27T07:30:00Z',
    updated_at: '2026-05-27T12:00:00Z',
  })
}

describe('useAppState', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    resetDbMocks()
  })

  it('bootstraps the current user workspace from auth and database tables', async () => {
    const { useAppState } = await import('@/composables/useAppState')
    const { loadEmotionRecords, state } = useAppState()

    await loadEmotionRecords()

    expect(authMock.ensureInitialized).toHaveBeenCalled()
    expect(dbMock.getProfile).toHaveBeenCalledWith('user-42')
    expect(dbMock.getEmotionDiaries).toHaveBeenCalledWith('user-42', 100)
    expect(dbMock.getAssessments).toHaveBeenCalledWith('user-42', 100)
    expect(state.currentAccountId).toBe('user-42')
    expect(state.profile).toEqual({
      phoneNumber: '13900000007',
      username: '数据库用户',
    })
    expect(state.diaries[0]).toMatchObject({
      id: 'diary-15',
      date: '2026-05-27',
      mood: 'good',
      content: '后端记录',
      triggers: ['运动'],
    })
  })

  it('creates a new emotion diary through the current db/api contract', async () => {
    const { useAppState } = await import('@/composables/useAppState')
    const { createEmotionRecord, loadEmotionRecords, state } = useAppState()
    await loadEmotionRecords()

    await createEmotionRecord({
      date: '2026-05-28',
      mood: 'bad',
      content: '晚上有些焦虑',
      triggers: ['工作压力'],
    })

    expect(dbMock.createEmotionDiary).toHaveBeenCalledWith({
      user_id: 'user-42',
      diary_date: '2026-05-28',
      emotion_level: 'bad',
      content: '晚上有些焦虑',
      tags: ['工作压力'],
      image_urls: [],
    })
    expect(state.diaries[0]).toMatchObject({
      id: 'diary-16',
      date: '2026-05-28',
      mood: 'bad',
      content: '晚上有些焦虑',
    })
  })

  it('updates the existing same-day diary instead of creating a duplicate', async () => {
    const { useAppState } = await import('@/composables/useAppState')
    const { createEmotionRecord, loadEmotionRecords, state } = useAppState()
    await loadEmotionRecords()

    await createEmotionRecord({
      date: '2026-05-27',
      mood: 'neutral',
      content: '更新后的记录',
      triggers: ['运动'],
    })

    expect(dbMock.updateEmotionDiary).toHaveBeenCalledWith('diary-15', {
      emotion_level: 'neutral',
      content: '更新后的记录',
      tags: ['运动'],
      image_urls: [],
    })
    expect(dbMock.createEmotionDiary).not.toHaveBeenCalled()
    expect(state.diaries[0]).toMatchObject({
      id: 'diary-15',
      mood: 'neutral',
      content: '更新后的记录',
    })
  })

})
