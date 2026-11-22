import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const appStateMock = vi.hoisted(() => ({
  state: {
    currentAccountId: 'profile-42',
    currentAccountRole: 'user',
    currentAccountCreatedAt: '2026-05-25T11:00:00Z',
    profile: { phoneNumber: '13900000007', username: '数据库用户' },
    diaries: [],
    assessments: [],
    knowledge: [],
    privacy: [],
    alerts: [],
    selectedDoctorId: '',
  },
  refreshCurrentAccountProfile: vi.fn(async () => {}),
  refreshAssessments: vi.fn(async () => []),
}))

const authSessionMock = vi.hoisted(() => ({
  state: {
    user: {
      id: 'profile-42',
      user_metadata: { role: 'user' },
    },
    profile: {
      id: 'profile-42',
      username: '数据库用户',
      phone: '13900000007',
      role: 'user',
      created_at: '2026-05-25T11:00:00Z',
      updated_at: '2026-05-25T11:00:00Z',
    },
  },
  signOut: vi.fn(async () => {}),
}))

vi.mock('@/composables/useAppState', () => ({
  useAppState: () => appStateMock,
}))

vi.mock('@/composables/useAuthSession', () => ({
  useAuthSession: () => authSessionMock,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

vi.mock('@/db/api', () => ({
  updateProfile: vi.fn(async (_id: string, updates: Record<string, unknown>) => ({
    id: 'profile-42',
    username: updates.username || '数据库用户',
    phone: updates.phone || '13900000007',
    role: 'user',
    created_at: '2026-05-25T11:00:00Z',
    updated_at: '2026-05-25T11:00:00Z',
  })),
  uploadUserAvatar: vi.fn(),
  uploadUserBackground: vi.fn(),
}))

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the current redesigned profile workspace from app state and auth profile', async () => {
    const ProfilePage = (await import('@/pages/user/ProfilePage.vue')).default
    const wrapper = mount(ProfilePage, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
        },
      },
    })

    expect(appStateMock.refreshCurrentAccountProfile).toHaveBeenCalled()
    expect(wrapper.text()).toContain('数据库用户')
    expect(wrapper.text()).toContain('健康报告')
    expect(wrapper.text()).toContain('手环数据')
    expect(wrapper.text()).toContain('对接管理员')
    expect(wrapper.text()).not.toContain('账号 ID')
  })
})
