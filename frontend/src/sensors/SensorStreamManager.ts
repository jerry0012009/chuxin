import type { SensorBatch, SensorSignal, SignalSnapshot } from '@/sensors/types'

interface SignalBuffer {
  signal: SensorSignal
  sampleRateHz: number
  channelNames: string[]
  values: Float32Array
  capacity: number
  channelCount: number
  cursor: number
  count: number
  latestSeq: number
}

export class SensorStreamManager {
  private readonly windowSeconds: number
  private readonly buffers = new Map<SensorSignal, SignalBuffer>()

  constructor(windowSeconds = 6) {
    this.windowSeconds = windowSeconds
  }

  push(batch: SensorBatch) {
    const channelCount = batch.channelNames.length
    const sampleCount = Math.floor(batch.samples.length / channelCount)
    const buffer = this.ensureBuffer(batch.signal, batch.sampleRateHz, batch.channelNames)

    for (let row = 0; row < sampleCount; row += 1) {
      const targetOffset = buffer.cursor * buffer.channelCount
      const sourceOffset = row * channelCount
      for (let channel = 0; channel < buffer.channelCount; channel += 1) {
        buffer.values[targetOffset + channel] = batch.samples[sourceOffset + channel] ?? Number.NaN
      }
      buffer.cursor = (buffer.cursor + 1) % buffer.capacity
      buffer.count = Math.min(buffer.count + 1, buffer.capacity)
    }
    buffer.latestSeq = batch.firstSeq + Math.max(0, sampleCount - 1)
  }

  snapshot(signal: SensorSignal, points = 120): SignalSnapshot | null {
    const buffer = this.buffers.get(signal)
    if (!buffer || buffer.count === 0) return null

    const channels = buffer.channelNames.map((name, channel) => {
      const ordered = new Float32Array(buffer.count)
      const start = (buffer.cursor - buffer.count + buffer.capacity) % buffer.capacity
      for (let index = 0; index < buffer.count; index += 1) {
        const row = (start + index) % buffer.capacity
        ordered[index] = buffer.values[row * buffer.channelCount + channel] ?? Number.NaN
      }
      const values = downsample(ordered, points)
      return {
        name,
        values,
        points: polylinePoints(values),
        latestValue: lastFinite(ordered),
      }
    })

    return {
      signal,
      sampleRateHz: buffer.sampleRateHz,
      channelNames: buffer.channelNames,
      channels,
      latestSeq: buffer.latestSeq,
    }
  }

  private ensureBuffer(signal: SensorSignal, sampleRateHz: number, channelNames: string[]) {
    const existing = this.buffers.get(signal)
    if (existing) return existing

    const capacity = Math.max(1, Math.ceil(sampleRateHz * this.windowSeconds))
    const channelCount = channelNames.length
    const buffer: SignalBuffer = {
      signal,
      sampleRateHz,
      channelNames,
      values: new Float32Array(capacity * channelCount),
      capacity,
      channelCount,
      cursor: 0,
      count: 0,
      latestSeq: 0,
    }
    this.buffers.set(signal, buffer)
    return buffer
  }
}

function downsample(values: Float32Array, points: number) {
  if (values.length <= points) return Array.from(values)

  const output: number[] = []
  const step = values.length / points
  for (let index = 0; index < points; index += 1) {
    const start = Math.floor(index * step)
    const end = Math.max(start + 1, Math.floor((index + 1) * step))
    let sum = 0
    let count = 0
    for (let source = start; source < end && source < values.length; source += 1) {
      const value = values[source] ?? Number.NaN
      if (Number.isFinite(value)) {
        sum += value
        count += 1
      }
    }
    output.push(count > 0 ? sum / count : Number.NaN)
  }
  return output
}

function lastFinite(values: Float32Array) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    const value = values[index] ?? Number.NaN
    if (Number.isFinite(value)) return value
  }
  return null
}

function polylinePoints(values: number[]) {
  if (values.length === 0) return ''

  const finiteValues = values.filter((value) => Number.isFinite(value))
  if (finiteValues.length === 0) return ''

  const min = Math.min(...finiteValues)
  const max = Math.max(...finiteValues)
  const range = max - min || 1
  const width = 320
  const height = 84
  const last = Math.max(1, values.length - 1)

  return values
    .map((value, index) => {
      const safeValue = Number.isFinite(value) ? value : min
      const x = (index / last) * width
      const y = height - ((safeValue - min) / range) * height
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}
