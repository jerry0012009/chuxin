import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import NeuropsychMobileControls from '@/components/neuropsych/NeuropsychMobileControls.vue'
import type { NeuropsychRecord } from '@/types'

const record = (overrides: Partial<NeuropsychRecord> = {}): NeuropsychRecord => ({
  id: 'record-1',
  test_id: 'test-1',
  user_id: 'user-1',
  source_type: 'self',
  status: 'in_progress',
  calc_status: 'none',
  warning_level: 'none',
  test_code: 'go-nogo-demo',
  test_title: 'Go-NoGo 体验版',
  ...overrides,
})

describe('NeuropsychMobileControls', () => {
  it('renders configured touch controls and emits the selected action', async () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({
          config_json: {
            mobileControls: [
              { id: 'continue', label: '开始/继续', type: 'command', command: 'advance', key: 'Enter', keyCode: 13, tone: 'secondary' },
              { id: 'respond', label: '反应', type: 'keypress', key: ' ', keyCode: 32, tone: 'primary' },
            ],
          },
        }),
      },
    })

    expect(wrapper.text()).toContain('移动端快捷操作')
    expect(wrapper.text()).toContain('继续')
    expect(wrapper.text()).toContain('反应')

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('trigger')?.[0]?.[0]).toMatchObject({ id: 'respond', keyCode: 32 })
  })

  it('falls back to discount left and right choices when config is absent', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'discount-titrate-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('选左侧')
    expect(wrapper.text()).toContain('选右侧')
    expect(wrapper.text()).toContain('继续')
  })

  it('keeps Columbia Card Task fallback compact because in-task buttons are touchable', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'columbia-card-task-hot-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('回车/继续')
    expect(wrapper.text()).not.toContain('翻一张')
    expect(wrapper.text()).not.toContain('不取牌')
  })

  it('falls back to Stroop color response controls when config is absent', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'stroop-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('红')
    expect(wrapper.text()).toContain('蓝')
    expect(wrapper.text()).toContain('绿')
    expect(wrapper.text()).toContain('开始/继续')
  })

  it('falls back to Flanker response controls when config is absent', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'flanker-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('F')
    expect(wrapper.text()).toContain('H')
    expect(wrapper.text()).toContain('开始/继续')
  })

  it('falls back to emotion regulation left and right choices when config is absent', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'emotion-regulation-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('选左侧')
    expect(wrapper.text()).toContain('选右侧')
  })

  it('keeps digit span fallback compact because the in-task number pad is touchable', () => {
    const wrapper = mount(NeuropsychMobileControls, {
      props: {
        record: record({ test_code: 'digit-span-demo', config_json: null }),
      },
    })

    expect(wrapper.text()).toContain('开始/继续')
    expect(wrapper.text()).not.toContain('选左侧')
  })
})
