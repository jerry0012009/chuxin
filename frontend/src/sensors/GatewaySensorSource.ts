import type { SensorBatch, SensorSourceStatus, SensorStreamSource } from '@/sensors/types'

interface GatewayMessage {
  type?: string
  batch?: {
    signal: SensorBatch['signal']
    sampleRateHz: number
    firstSeq: number
    startedAtMs?: number
    channelNames: string[]
    samples: number[][]
    rawChannelNames?: string[]
    rawSamples?: number[][]
    status?: number
  }
}

interface GatewaySensorSourceOptions {
  url?: string
  includeRawSamples?: boolean
}

export class GatewaySensorSource implements SensorStreamSource {
  private readonly listeners = new Set<(batch: SensorBatch) => void>()
  private readonly statusListeners = new Set<(status: SensorSourceStatus) => void>()
  private status: SensorSourceStatus = 'idle'
  private socket: WebSocket | null = null
  private reconnectTimer: number | null = null
  private shouldReconnect = false
  private connectPromise: Promise<void> | null = null
  private readonly url: string
  private readonly includeRawSamples: boolean

  constructor(options: GatewaySensorSourceOptions = {}) {
    this.url = options.url || resolveGatewayUrl()
    this.includeRawSamples = options.includeRawSamples ?? false
  }

  connect() {
    this.shouldReconnect = true
    if (this.status === 'connected') return Promise.resolve()
    if (this.connectPromise) return this.connectPromise

    this.setStatus('connecting')
    this.connectPromise = new Promise<void>((resolve, reject) => {
      const socket = new WebSocket(this.url)
      this.socket = socket
      let settled = false

      socket.onopen = () => {
        settled = true
        this.connectPromise = null
        this.setStatus('connected')
        resolve()
      }

      socket.onmessage = (event) => {
        const batch = parseBatch(event.data, this.includeRawSamples)
        if (!batch) return
        for (const listener of this.listeners) listener(batch)
      }

      socket.onerror = () => {
        this.setStatus('error')
        if (!settled) {
          settled = true
          this.connectPromise = null
          reject(new Error('传感器网关连接失败'))
        }
      }

      socket.onclose = () => {
        if (this.socket === socket) {
          this.socket = null
          this.connectPromise = null
          this.setStatus(this.shouldReconnect ? 'connecting' : 'idle')
          this.scheduleReconnect()
          if (!settled) {
            settled = true
            reject(new Error('传感器网关连接已断开'))
          }
        }
      }
    })
    return this.connectPromise
  }

  disconnect() {
    this.shouldReconnect = false
    this.clearReconnectTimer()
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.connectPromise = null
    this.setStatus('idle')
  }

  reconnect() {
    this.shouldReconnect = true
    this.clearReconnectTimer()
    if (this.socket) {
      const socket = this.socket
      this.socket = null
      socket.close()
    }
    this.connectPromise = null
    this.setStatus('idle')
    return this.connect()
  }

  subscribe(listener: (batch: SensorBatch) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  subscribeStatus(listener: (status: SensorSourceStatus) => void) {
    this.statusListeners.add(listener)
    listener(this.status)
    return () => this.statusListeners.delete(listener)
  }

  getStatus() {
    return this.status
  }

  private setStatus(status: SensorSourceStatus) {
    if (this.status === status) return
    this.status = status
    for (const listener of this.statusListeners) listener(status)
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect || this.reconnectTimer !== null) return
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      if (!this.shouldReconnect || this.socket || this.connectPromise) return
      void this.connect().catch(() => {
        this.scheduleReconnect()
      })
    }, 1000)
  }

  private clearReconnectTimer() {
    if (this.reconnectTimer === null) return
    window.clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
  }
}

function resolveGatewayUrl() {
  const configured = import.meta.env.VITE_SENSOR_GATEWAY_WS
  if (configured) return configured

  const base = import.meta.env.BASE_URL || '/'
  const prefix = base.replace(/\/$/, '')
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${prefix}/sensor-gateway/ws`
}

function parseBatch(raw: unknown, includeRawSamples: boolean): SensorBatch | null {
  if (typeof raw !== 'string') return null

  let message: GatewayMessage
  try {
    message = JSON.parse(raw) as GatewayMessage
  } catch {
    return null
  }

  if (message.type !== 'sensor_batch' || !message.batch) return null
  const { batch } = message
  if (!Array.isArray(batch.samples) || !Array.isArray(batch.channelNames)) return null

  const flat = flattenSamples(batch.samples, batch.channelNames.length)
  const rawSamples = includeRawSamples && Array.isArray(batch.rawSamples) && Array.isArray(batch.rawChannelNames)
    ? flattenSamples(batch.rawSamples, batch.rawChannelNames.length)
    : undefined

  return {
    signal: batch.signal,
    sampleRateHz: batch.sampleRateHz,
    firstSeq: batch.firstSeq,
    startedAtMs: batch.startedAtMs || Date.now(),
    channelNames: batch.channelNames,
    samples: flat,
    rawChannelNames: includeRawSamples ? batch.rawChannelNames : undefined,
    rawSamples,
    status: Number.isFinite(Number(batch.status)) ? Number(batch.status) : undefined,
  }
}

function flattenSamples(samples: number[][], channelCount: number) {
  const flat = new Float32Array(samples.length * channelCount)
  for (let row = 0; row < samples.length; row += 1) {
    const sample = samples[row] || []
    for (let channel = 0; channel < channelCount; channel += 1) {
      const value = Number(sample[channel])
      flat[row * channelCount + channel] = Number.isFinite(value) ? value : Number.NaN
    }
  }
  return flat
}
