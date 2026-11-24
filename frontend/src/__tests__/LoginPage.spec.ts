import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginPage from '@/pages/auth/LoginPage.vue'
import { useAuthSession } from '@/composables/useAuthSession'

const replace = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    replace,
  }),
}))

vi.mock('@/db/api', () => ({
  getDepartments: vi.fn(async () => []),
}))

vi.mock('@/composables/useAuthSession', () => {
  const state = {
    profile: null as null | { role: 'user' | 'doctor' | 'admin' | 'super_admin' },
  }
  return {
    useAuthSession: () => ({
      state,
      signInWithUsername: vi.fn(async (username: string) => {
        state.profile = {
          role: username.includes('super') ? 'super_admin' : username.includes('admin') ? 'admin' : username.includes('doctor') ? 'doctor' : 'user',
        }
        return { error: null }
      }),
      signUpWithUsername: vi.fn(async (payload: { role?: 'user' | 'doctor' }) => {
        state.profile = { role: payload.role || 'user' }
        return { error: null }
      }),
    }),
  }
})

describe('LoginPage', () => {
  beforeEach(() => {
    replace.mockClear()
    window.history.replaceState({}, '', '/')
  })

  afterEach(() => {
    replace.mockClear()
    window.history.replaceState({}, '', '/')
  })

  it('matches xinyu-care public role boundary without admin tab', () => {
    const wrapper = mount(LoginPage)

    expect(wrapper.get('[data-testid="role-user"]').text()).toContain('用户端')
    expect(wrapper.get('[data-testid="role-doctor"]').text()).toContain('管理员端')
    expect(wrapper.find('[data-testid="role-admin"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('超级管理员')
  })

  it('redirects backend admin profile to doctor dashboard without exposing admin selector', async () => {
    const wrapper = mount(LoginPage)

    await wrapper.get('[data-testid="username-input"]').setValue('admin-account')
    await wrapper.get('[data-testid="password-input"]').setValue('123456')
    await wrapper.get('form').trigger('submit.prevent')

    expect(replace).toHaveBeenCalledWith('/admin/dashboard')
    expect(useAuthSession().state.profile?.role).toBe('admin')
  })

  it('redirects super admin profile to the unified admin dashboard', async () => {
    const wrapper = mount(LoginPage)

    await wrapper.get('[data-testid="username-input"]').setValue('super-admin')
    await wrapper.get('[data-testid="password-input"]').setValue('123456')
    await wrapper.get('form').trigger('submit.prevent')

    expect(replace).toHaveBeenCalledWith('/admin/dashboard')
    expect(useAuthSession().state.profile?.role).toBe('super_admin')
  })

  it('submits doctor registration with verification code and redirects to doctor dashboard', async () => {
    const wrapper = mount(LoginPage)

    await wrapper.get('[data-testid="role-doctor"]').trigger('click')
    await wrapper.get('[data-testid="mode-register"]').trigger('click')
    await wrapper.get('[data-testid="username-input"]').setValue('doctor-li')
    await wrapper.get('[data-testid="password-input"]').setValue('123456')
    await wrapper.get('[data-testid="verification-code-input"]').setValue('2026')
    await wrapper.get('form').trigger('submit.prevent')

    expect(replace).toHaveBeenCalledWith('/admin/dashboard')
  })

  it('redirects user login to xinyu-care default home or route state target', async () => {
    const wrapper = mount(LoginPage)

    await wrapper.get('[data-testid="username-input"]').setValue('regular-user')
    await wrapper.get('[data-testid="password-input"]').setValue('123456')
    await wrapper.get('form').trigger('submit.prevent')
    expect(replace).toHaveBeenCalledWith('/')

    replace.mockClear()
    window.history.replaceState({ from: '/record' }, '', '/login')
    const redirectedWrapper = mount(LoginPage)
    await redirectedWrapper.get('[data-testid="username-input"]').setValue('regular-user')
    await redirectedWrapper.get('[data-testid="password-input"]').setValue('123456')
    await redirectedWrapper.get('form').trigger('submit.prevent')
    expect(replace).toHaveBeenCalledWith('/record')
  })

  it('ignores query redirect and only honors router state like xinyu-care', async () => {
    window.history.replaceState({}, '', '/login?redirect=/record')
    const wrapper = mount(LoginPage)

    await wrapper.get('[data-testid="username-input"]').setValue('regular-user')
    await wrapper.get('[data-testid="password-input"]').setValue('123456')
    await wrapper.get('form').trigger('submit.prevent')

    expect(replace).toHaveBeenCalledWith('/')
  })
})
