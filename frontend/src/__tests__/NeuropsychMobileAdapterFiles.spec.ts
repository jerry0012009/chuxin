import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(process.cwd(), 'public/neuropsych')
const read = (path: string) => readFileSync(resolve(root, path), 'utf8')

describe('neuropsych mobile adapter files', () => {
  it('provides the shared adapter, styles, and presets', () => {
    expect(read('mobile-adapter/adapter.js')).toContain('window.ChuxinMobileAdapter')
    expect(read('mobile-adapter/presets.js')).toContain('go-nogo-demo')
    expect(read('mobile-adapter/presets.js')).toContain('discount-titrate-demo')
    expect(read('mobile-adapter/presets.js')).toContain('columbia-card-task-hot-demo')
    expect(read('mobile-adapter/presets.js')).toContain("'stroop': stroopPreset")
    expect(read('mobile-adapter/presets.js')).toContain("'stroop-demo': stroopPreset")
    expect(read('mobile-adapter/presets.js')).toContain("'flanker': flankerPreset")
    expect(read('mobile-adapter/presets.js')).toContain("'emotion-regulation': emotionRegulationPreset")
    expect(read('mobile-adapter/presets.js')).toContain("'digit-span': digitSpanPreset")
    expect(read('mobile-adapter/adapter.js')).toContain('if (!isTouchLike) return')
    expect(read('mobile-adapter/base.css')).toContain('chuxin-layout-two-choice')
    expect(read('mobile-adapter/base.css')).toContain('chuxin-layout-card-grid')
    expect(read('mobile-adapter/base.css')).toContain('chuxin-layout-digit-grid')
  })

  it('wires the first demo experiments into the adapter kit', () => {
    for (const code of ['go-nogo-demo', 'discount-titrate-demo', 'columbia-card-task-hot-demo', 'stroop-demo', 'emotion-regulation-demo', 'digit-span-demo', 'flanker-demo']) {
      const html = read(`expfactory/${code}/index.html`)
      expect(html).toContain(`data-chuxin-test='${code}'`)
      expect(html).toContain('../../mobile-adapter/base.css')
      expect(html).toContain('../../mobile-adapter/presets.js')
      expect(html).toContain('../../mobile-adapter/adapter.js')
      expect(html).toContain('fullscreen: false')
    }
  })

  it('guards old jsPsych image preloading against functions and HTML stimuli', () => {
    for (const code of ['go-nogo-demo', 'discount-titrate-demo', 'columbia-card-task-hot-demo']) {
      const jspsych = read(`expfactory/${code}/js/jspsych/jspsych.js`)
      expect(jspsych).toContain('normalizeImagePreloadList')
      expect(jspsych).toContain("typeof item !== 'string'")
      expect(jspsych).toContain('srcRegex')
    }
  })
})
