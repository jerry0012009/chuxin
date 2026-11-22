import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routerPush = vi.fn()
const signOut = vi.fn()
const authState = vi.hoisted(() => ({
  value: {
    initialized: true,
    user: { id: 'doctor-1' },
    profile: {
      username: '当前管理员',
      full_name: '当前管理员',
      role: 'doctor',
    },
  },
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/admin/dashboard' }),
  useRouter: () => ({
    push: routerPush,
  }),
  RouterLink: {
    props: ['to'],
    template: '<a :href="typeof to === \'string\' ? to : to.path"><slot /></a>',
  },
  RouterView: {
    template: '<main data-testid="router-view" />',
  },
}))

vi.mock('@/composables/useAuthSession', () => ({
  useAuthSession: () => ({
    state: authState.value,
    ensureInitialized: vi.fn(async () => {}),
    signOut,
  }),
}))

describe('role workspace layouts', () => {
  beforeEach(() => {
    authState.value = {
      initialized: true,
      user: { id: 'doctor-1' },
      profile: {
        username: '当前管理员',
        full_name: '当前管理员',
        role: 'doctor',
      },
    }
    routerPush.mockClear()
    signOut.mockClear()
  })

  it('shows the doctor sidebar entries including assessment publishing and neuropsych workspaces', () => {
    const wrapper = mount(AdminLayout)

    expect(wrapper.text()).not.toContain('返回用户端')
    expect(wrapper.text()).not.toContain('超级管理员')
    expect(wrapper.text()).toContain('管理员后台')
    expect(wrapper.text()).toContain('数据看板')
    expect(wrapper.text()).toContain('用户管理')
    expect(wrapper.text()).toContain('发布测评任务')
    expect(wrapper.text()).toContain('量表测评')
    expect(wrapper.text()).toContain('神经心理测评')
    expect(wrapper.text()).toContain('知识库')
    expect(wrapper.text()).toContain('预警消息')
  })

  it('signs out from the doctor sidebar and returns to login', async () => {
    const wrapper = mount(AdminLayout)

    const logoutButton = wrapper.findAll('button').find((button) => button.text().includes('退出登录'))
    expect(logoutButton).toBeTruthy()

    await logoutButton!.trigger('click')

    expect(signOut).toHaveBeenCalledOnce()
    expect(routerPush).toHaveBeenCalledWith('/login')
  })

  it('shows the current authenticated doctor in the sidebar account summary', () => {
    authState.value.profile = {
      username: 'doctor-li',
      full_name: '李管理员',
      role: 'doctor',
    }

    const wrapper = mount(AdminLayout)

    expect(wrapper.text()).toContain('李管理员')
    expect(wrapper.text()).toContain('管理员')
  })

  it('shows department management alongside admin workspaces for super admin', () => {
    authState.value.profile = {
      username: 'admin',
      full_name: '超级管理员',
      role: 'super_admin',
    }

    const wrapper = mount(AdminLayout)

    expect(wrapper.text()).toContain('超级管理员')
    expect(wrapper.text()).toContain('数据看板')
    expect(wrapper.text()).toContain('用户管理')
    expect(wrapper.text()).toContain('部门管理')
  })
})
