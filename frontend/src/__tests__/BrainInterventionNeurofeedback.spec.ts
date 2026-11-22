import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const routeState = vi.hoisted(() => ({
  params: {} as Record<string, string>,
  path: '/brain-intervention',
  query: {} as Record<string, string>,
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/db/api', () => ({
  completeInterventionItem: vi.fn(),
  startInterventionItem: vi.fn(async () => {}),
  createBrainInterventionReport: vi.fn(async () => ({ id: 'report-1' })),
  getHealingContents: vi.fn(async () => []),
}))

describe('BrainInterventionPage neurofeedback demo', () => {
  beforeEach(() => {
    routeState.params = {}
    routeState.path = '/brain-intervention'
    routeState.query = {}
  })

  it('renders the signal monitor by default when opening brain intervention from the sidebar', async () => {
    const BrainInterventionPage = (await import('@/pages/user/BrainInterventionPage.vue')).default
    const wrapper = mount(BrainInterventionPage, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
          RealtimeSignalPanel: {
            template: '<section data-testid="realtime-signal-panel" />',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('神经反馈训练')
    expect(wrapper.text()).toContain('实时生理信号')
    expect(wrapper.text()).not.toContain('Web EEG Neurofeedback Training Demo')
    expect(wrapper.get('[data-testid="realtime-signal-panel"]').attributes('data-testid')).toBe('realtime-signal-panel')
  })

  it('renders neurofeedback when the neurofeedback mode is selected', async () => {
    routeState.params = { mode: 'neurofeedback' }
    routeState.path = '/brain-intervention/neurofeedback'
    const BrainInterventionPage = (await import('@/pages/user/BrainInterventionPage.vue')).default
    const wrapper = mount(BrainInterventionPage, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
          RealtimeSignalPanel: {
            template: '<section data-testid="realtime-signal-panel" />',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('Web EEG Neurofeedback Training Demo')
    expect(wrapper.text()).toContain('Alpha 8–12Hz')
    expect(wrapper.find('[data-testid="realtime-signal-panel"]').exists()).toBe(false)
  })

  it('renders the realtime signal panel when the signal monitor mode is selected', async () => {
    routeState.params = { mode: 'signals' }
    routeState.path = '/brain-intervention/signals'
    const BrainInterventionPage = (await import('@/pages/user/BrainInterventionPage.vue')).default
    const wrapper = mount(BrainInterventionPage, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
          RealtimeSignalPanel: {
            template: '<section data-testid="realtime-signal-panel" />',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('实时生理信号')
    expect(wrapper.text()).not.toContain('Web EEG Neurofeedback Training Demo')
    expect(wrapper.get('[data-testid="realtime-signal-panel"]').attributes('data-testid')).toBe('realtime-signal-panel')
  })

  it('renders the biosignal meditation task as an independent brain intervention mode', async () => {
    routeState.params = { mode: 'meditation' }
    routeState.path = '/brain-intervention/meditation'
    const BrainInterventionPage = (await import('@/pages/user/BrainInterventionPage.vue')).default
    const wrapper = mount(BrainInterventionPage, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a><slot /></a>',
          },
          BiosignalMeditationDemo: {
            template: '<section data-testid="biosignal-meditation-demo">脑机交互冥想</section>',
          },
          RealtimeSignalPanel: {
            template: '<section data-testid="realtime-signal-panel" />',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('脑机交互冥想')
    expect(wrapper.get('[data-testid="biosignal-meditation-demo"]').attributes('data-testid')).toBe('biosignal-meditation-demo')
    expect(wrapper.find('[data-testid="realtime-signal-panel"]').exists()).toBe(false)
  })
})
