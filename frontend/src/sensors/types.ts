export type SensorSignal = 'eeg' | 'ppg' | 'gsr'

export type SensorSourceStatus = 'idle' | 'connecting' | 'connected' | 'error'

export interface SensorBatch {
  signal: SensorSignal
  sampleRateHz: number
  firstSeq: number
  startedAtMs: number
  channelNames: string[]
  samples: Float32Array
  rawChannelNames?: string[]
  rawSamples?: Float32Array
  status?: number
}

export interface SensorStreamSource {
  connect(): Promise<void>
  disconnect(): void
  subscribe(listener: (batch: SensorBatch) => void): () => void
  getStatus(): SensorSourceStatus
}

export interface SignalSnapshot {
  signal: SensorSignal
  sampleRateHz: number
  channelNames: string[]
  channels: SignalChannelSnapshot[]
  latestSeq: number
}

export interface SignalChannelSnapshot {
  name: string
  values: number[]
  latestValue: number | null
  points?: string
}
