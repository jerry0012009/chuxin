<script setup lang="ts">
import { Activity, Brain, Droplets, Loader2 } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { GatewaySensorSource } from '@/sensors/GatewaySensorSource'
import { SensorStreamManager } from '@/sensors/SensorStreamManager'
import type { SensorSignal, SignalSnapshot } from '@/sensors/types'

interface SignalCard {
  signal: SensorSignal
  title: string
  color: string
  icon: unknown
}

const signalCards: SignalCard[] = [
  { signal: 'eeg', title: '脑电 EEG', color: '#0891b2', icon: Brain },
  { signal: 'ppg', title: '心率 PPG', color: '#e11d48', icon: Activity },
  { signal: 'gsr', title: '皮肤电 GSR', color: '#0d9488', icon: Droplets },
]

const source = new GatewaySensorSource()
const windowSeconds = 8
const manager = new SensorStreamManager(windowSeconds)
const repaintIntervalMs = 500
const connected = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const frameTick = ref(0)

let unsubscribe: (() => void) | null = null
let unsubscribeStatus: (() => void) | null = null
let repaintFrame = 0
let heartbeatTimer = 0
let lastBatchAt = 0
let lastRepaintAt = 0

const snapshots = computed(() => {
  frameTick.value
  return signalCards.map((card) => ({
    ...card,
    snapshot: manager.snapshot(card.signal, 64),
  }))
})

const statusText = computed(() => {
  if (loading.value) return '正在连接数据源'
  if (connected.value) return '信号接收中'
  if (errorMessage.value) return '数据源异常'
  return '等待信号'
})

const requestRepaint = () => {
  if (repaintFrame) return
  const waitMs = Math.max(0, repaintIntervalMs - (Date.now() - lastRepaintAt))
  repaintFrame = window.setTimeout(() => {
    repaintFrame = 0
    window.requestAnimationFrame(() => {
      lastRepaintAt = Date.now()
      frameTick.value += 1
    })
  }, waitMs)
}

const start = async () => {
  if (connected.value || loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    if (!unsubscribe) {
      unsubscribe = source.subscribe((batch) => {
        lastBatchAt = Date.now()
        manager.push(batch)
        requestRepaint()
        if (errorMessage.value === '信号暂时中断，正在重连') {
          errorMessage.value = ''
        }
      })
    }
    if (!unsubscribeStatus) {
      unsubscribeStatus = source.subscribeStatus((status) => {
        connected.value = status === 'connected'
        if (status === 'connecting' && lastBatchAt > 0) {
          errorMessage.value = '信号暂时中断，正在重连'
        }
      })
    }
    await source.connect()
    connected.value = true
    requestRepaint()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '传感器数据加载失败'
  } finally {
    loading.value = false
  }
}

const disconnect = () => {
  source.disconnect()
  connected.value = false
  if (repaintFrame) {
    window.clearTimeout(repaintFrame)
    repaintFrame = 0
  }
  if (heartbeatTimer) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = 0
  }
  if (unsubscribe) unsubscribe()
  unsubscribe = null
  if (unsubscribeStatus) unsubscribeStatus()
  unsubscribeStatus = null
}

const formatValue = (name: string, value: number | null) => {
  if (value === null || !Number.isFinite(value)) return '--'
  const digits = name.includes('_V') || name.includes('Ratio') ? 4 : Math.abs(value) >= 100 ? 0 : 2
  return value.toFixed(digits)
}

const channelUnit = (name: string) => {
  if (name.endsWith('_uV')) return 'uV'
  if (name.endsWith('_mV')) return 'mV'
  if (name.endsWith('_V')) return 'V'
  if (name.endsWith('_bpm')) return 'bpm'
  if (name.endsWith('_pct')) return '%'
  return ''
}

const displayName = (name: string) => name
  .replace(/^CH(\d+)_processed_uV$/, 'CH$1 电位')
  .replace('HR_bpm', '心率')
  .replace('SpO2_pct', '血氧估算')
  .replace('SpO2_RatioR', '血氧比值 R')
  .replace('GSR_display_mV', '皮肤电显示值')
  .replace('GSR_display_V', '皮肤电显示电压')
  .replace('GSR_physical_mV', '皮肤电物理值')
  .replace('GSR_physical_V', '皮肤电物理电压')

const plottedChannels = (snapshot: SignalSnapshot | null) => {
  if (!snapshot) return []
  if (snapshot.signal === 'eeg') return snapshot.channels.filter((channel) => channel.name.endsWith('_processed_uV'))
  if (snapshot.signal === 'ppg') return snapshot.channels.filter((channel) => ['HR_bpm', 'SpO2_pct'].includes(channel.name))
  if (snapshot.signal === 'gsr') return snapshot.channels.filter((channel) => channel.name === 'GSR_display_mV')
  return []
}

const highlightChannels = (snapshot: SignalSnapshot | null) => {
  if (!snapshot) return []
  if (snapshot.signal === 'ppg') return snapshot.channels.filter((channel) => channel.name === 'SpO2_RatioR')
  if (snapshot.signal === 'gsr') return snapshot.channels.filter((channel) => channel.name === 'GSR_display_V')
  return []
}

onMounted(() => {
  void start()
  heartbeatTimer = window.setInterval(() => {
    if (lastBatchAt > 0 && Date.now() - lastBatchAt > 3000) {
      connected.value = false
      errorMessage.value = '信号暂时中断，正在重连'
      void source.reconnect().catch(() => {
        errorMessage.value = '信号暂时中断，正在重连'
      })
    }
  }, 1000)
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<template>
  <section class="rounded-[28px] border border-slate-100 bg-white p-5 shadow-lg shadow-cyan-100/40 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none" data-testid="realtime-signal-panel">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div class="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-200">
          <span class="h-2 w-2 rounded-full" :class="connected ? 'bg-emerald-500' : 'bg-slate-300'" />
          {{ statusText }}
        </div>
        <h2 class="mt-3 text-xl font-black text-slate-900 dark:text-white">实时生理信号</h2>
      </div>

      <div class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        最近 {{ windowSeconds }} 秒窗口
      </div>
    </div>

    <div v-if="errorMessage" class="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">
      {{ errorMessage }}
    </div>

    <div class="mt-5 grid gap-4 xl:grid-cols-3">
      <article v-for="item in snapshots" :key="item.signal" class="rounded-2xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-black text-slate-900 dark:text-white">{{ item.title }}</p>
            <p class="mt-1 text-xs font-bold text-slate-500">{{ item.snapshot?.sampleRateHz || '--' }} Hz · Seq {{ item.snapshot?.latestSeq || '--' }}</p>
          </div>
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white shadow-sm dark:bg-slate-900" :style="{ color: item.color }">
            <component :is="item.icon" class="h-5 w-5" />
          </div>
        </div>

        <div class="mt-4 space-y-2">
          <div v-for="channel in plottedChannels(item.snapshot)" :key="channel.name" class="rounded-xl bg-white p-3 dark:bg-slate-900">
            <div class="mb-2 flex items-center justify-between gap-3">
              <span class="truncate text-xs font-black text-slate-600 dark:text-slate-300">{{ displayName(channel.name) }}</span>
              <span class="shrink-0 text-xs font-bold text-slate-400">{{ formatValue(channel.name, channel.latestValue) }} {{ channelUnit(channel.name) }}</span>
            </div>
            <svg class="h-14 w-full overflow-visible" viewBox="0 0 320 84" preserveAspectRatio="none" role="img" aria-label="实时波形">
              <line x1="0" y1="42" x2="320" y2="42" class="stroke-slate-100 dark:stroke-slate-800" stroke-width="1" />
              <polyline v-if="channel.points" :points="channel.points" fill="none" :stroke="item.color" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" />
            </svg>
          </div>
        </div>

        <div v-if="highlightChannels(item.snapshot).length > 0" class="mt-4 grid grid-cols-2 gap-2">
          <div v-for="channel in highlightChannels(item.snapshot)" :key="channel.name" class="rounded-xl bg-white px-3 py-2 dark:bg-slate-900">
            <p class="truncate text-[11px] font-bold text-slate-400">{{ displayName(channel.name) }}</p>
            <p class="mt-1 truncate text-sm font-black text-slate-900 dark:text-white">{{ formatValue(channel.name, channel.latestValue) }} {{ channelUnit(channel.name) }}</p>
          </div>
        </div>

      </article>
    </div>
  </section>
</template>
