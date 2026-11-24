import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import WebEegNeurofeedbackDemo from '@/components/neurofeedback/WebEegNeurofeedbackDemo.vue'
import type { VueWrapper } from '@vue/test-utils'
const createBrainInterventionReport = vi.hoisted(() => vi.fn(async () => ({ id: 'report-1' })))

vi.mock('@/db/api', () => ({
  createBrainInterventionReport,
}))

describe('WebEegNeurofeedbackDemo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('runs the alpha training flow and switches metrics', async () => {
    const wrapper = mount(WebEegNeurofeedbackDemo)

    expect(wrapper.text()).toContain('实时神经反馈训练')
    expect(wrapper.text()).toContain('Alpha 8–12Hz')
    expect(wrapper.text()).toContain('连接与信号检查')

    await buttonByText(wrapper, '开始训练').trigger('click')
    await vi.advanceTimersByTimeAsync(1200)
    await vi.advanceTimersByTimeAsync(0)

    expect(wrapper.text()).toContain('暂停')
    expect(wrapper.text()).not.toContain('0.0')

    await vi.advanceTimersByTimeAsync(10000)
    expect(wrapper.text()).toContain('基线采集')

    await vi.advanceTimersByTimeAsync(15000)
    expect(wrapper.text()).toContain('反馈训练')

    await vi.advanceTimersByTimeAsync(30000)
    await vi.advanceTimersByTimeAsync(30000)
    expect(wrapper.text()).toContain('训练完成')
    expect(wrapper.text()).toContain('100%')
    expect(createBrainInterventionReport).toHaveBeenCalled()

    const polyline = wrapper.get('svg[aria-label*="反馈值趋势"] polyline')
    expect(polyline.attributes('points')?.trim().split(/\s+/).length).toBe(120)

    await buttonByText(wrapper, '重置').trigger('click')
    expect(wrapper.text()).toContain('连接与信号检查')
    expect(wrapper.text()).toContain('0')

    await buttonByText(wrapper, 'Beta 13–30Hz').trigger('click')
    expect(wrapper.text()).toContain('Beta 13–30Hz')
    expect(wrapper.text()).toContain('清醒度 / 任务投入')
  })
})

function buttonByText(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text().includes(text))
  if (!button) throw new Error(`button not found: ${text}`)
  return button
}
