export type NeurofeedbackMetric = 'alpha' | 'theta' | 'beta' | 'smr' | 'thetaBetaRatio'

export interface NeurofeedbackFeatureSample {
  metric: NeurofeedbackMetric
  value: number
  timestampMs: number
}

export interface NeurofeedbackFeatureSource {
  start(metric: NeurofeedbackMetric, onSample: (sample: NeurofeedbackFeatureSample) => void): void
  stop(): void
}

const metricProfiles: Record<NeurofeedbackMetric, { base: number; lift: number; wave: number; speed: number }> = {
  alpha: { base: 44, lift: 30, wave: 5, speed: 0.11 },
  theta: { base: 50, lift: 10, wave: 9, speed: 0.07 },
  beta: { base: 54, lift: 8, wave: 7, speed: 0.16 },
  smr: { base: 52, lift: 13, wave: 4, speed: 0.09 },
  thetaBetaRatio: { base: 48, lift: 12, wave: 6, speed: 0.08 },
}

export class MockNeurofeedbackFeatureSource implements NeurofeedbackFeatureSource {
  private timer: number | null = null
  private value = 48
  private tick = 0

  constructor(private readonly intervalMs = 400) {}

  start(metric: NeurofeedbackMetric, onSample: (sample: NeurofeedbackFeatureSample) => void) {
    this.stop()
    this.value = metric === 'alpha' ? 45 : 50
    this.tick = 0
    this.timer = window.setInterval(() => {
      const profile = metricProfiles[metric]
      const lift = profile.lift * (1 - Math.exp(-this.tick / 90))
      const wave = Math.sin(this.tick * profile.speed) * profile.wave
      const noise = (Math.random() - 0.5) * 3
      const target = profile.base + lift + wave + noise
      this.value = clamp(this.value + (target - this.value) * 0.18, 0, 100)
      this.tick += 1
      onSample({
        metric,
        value: this.value,
        timestampMs: Date.now(),
      })
    }, this.intervalMs)
  }

  stop() {
    if (this.timer !== null) {
      window.clearInterval(this.timer)
      this.timer = null
    }
  }
}

export class EegWebSocketFeatureSource implements NeurofeedbackFeatureSource {
  constructor(private readonly url: string) {}

  start(_metric: NeurofeedbackMetric, _onSample: (sample: NeurofeedbackFeatureSample) => void) {
    this.stop()
    throw new Error(`真实 EEG 特征流入口已预留：${this.url}。后续在这里接入 500Hz/100ms batch，并计算 band power。`)
  }

  stop() {}
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}
