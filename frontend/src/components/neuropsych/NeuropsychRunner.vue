<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Loader2, X } from 'lucide-vue-next'
import NeuropsychMobileControls from '@/components/neuropsych/NeuropsychMobileControls.vue'
import type { NeuropsychMobileControlAction, NeuropsychRecord } from '@/types'

const props = defineProps<{
  record: NeuropsychRecord
  submitting?: boolean
}>()

const emit = defineEmits<{
  close: []
  finished: [{ rawJson: string; rawCsv?: string; testCode?: string }]
}>()

const received = ref(false)
const iframeRef = ref<HTMLIFrameElement | null>(null)
const controlNotice = ref('')
let noticeTimer: number | null = null

const sourceUrl = computed(() => {
  const path = props.record.source_path || `neuropsych/expfactory/${props.record.test_code}/index.html`
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${path}`.replace(/([^:]\/)\/+/g, '$1')
})

const handleMessage = (event: MessageEvent) => {
  if (event.origin !== window.location.origin) return
  const data = event.data
  if (!data || data.type !== 'chuxin-neuropsych-finished') return
  received.value = true
  emit('finished', {
    rawJson: data.rawJson,
    rawCsv: data.rawCsv,
    testCode: data.testCode,
  })
}

const showControlNotice = (message: string) => {
  controlNotice.value = message
  if (noticeTimer !== null) window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    controlNotice.value = ''
    noticeTimer = null
  }, 1400)
}

const iframeDocument = () => iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document || null
const iframeAdapter = () => (iframeRef.value?.contentWindow as any)?.ChuxinMobileAdapter || null

const dispatchKey = (action: NeuropsychMobileControlAction, silent = false) => {
  const adapter = iframeAdapter()
  if (adapter?.sendKey) {
    const ok = Boolean(adapter.sendKey({ key: action.key, code: action.code, keyCode: action.keyCode }))
    if (!silent) showControlNotice(ok ? `已发送：${action.label}` : '当前步骤暂不可用')
    return ok
  }

  const win = iframeRef.value?.contentWindow
  const doc = iframeDocument()
  if (!win || !doc) {
    if (!silent) showControlNotice('实验还在加载')
    return false
  }

  const keyCode = action.keyCode || 13
  const key = action.key || (keyCode === 32 ? ' ' : 'Enter')
  const code = action.code || (keyCode === 32 ? 'Space' : keyCode === 13 ? 'Enter' : '')
  for (const type of ['keydown', 'keyup']) {
    const event = new KeyboardEvent(type, { key, code, bubbles: true, cancelable: true })
    Object.defineProperty(event, 'keyCode', { get: () => keyCode })
    Object.defineProperty(event, 'which', { get: () => keyCode })
    Object.defineProperty(event, 'charCode', { get: () => keyCode })
    doc.dispatchEvent(event)
    doc.body?.dispatchEvent(event)
    win.dispatchEvent(event)
  }
  if (!silent) showControlNotice(`已发送：${action.label}`)
  return true
}

const clickBySelectors = (selectors: string[] = []) => {
  const doc = iframeDocument()
  if (!doc) return false
  for (const selector of selectors) {
    const target = doc.querySelector<HTMLElement>(selector)
    if (target && !target.hasAttribute('disabled')) {
      target.click()
      return true
    }
  }
  return false
}

const runCommand = (action: NeuropsychMobileControlAction) => {
  const doc = iframeDocument()
  if (!doc) return false
  const adapter = iframeAdapter()
  if (action.command === 'advance') {
    if (adapter?.advance) return Boolean(adapter.advance())
    return clickBySelectors([
      '#jspsych-fullscreen-btn:not(:disabled)',
      '#jspsych-instructions-next:not(:disabled)',
      '.jspsych-btn:not(:disabled)',
    ]) || dispatchKey(action, true)
  }
  if (action.command === 'clickFirstAvailableCard') {
    if (adapter?.clickFirstAvailableCard) return Boolean(adapter.clickFirstAvailableCard())
    const target = doc.querySelector<HTMLElement>('.card_image.select-button:not(:disabled), input.card_image:not(:disabled)')
    if (target) {
      target.click()
      return true
    }
  }
  return false
}

const triggerMobileAction = (action: NeuropsychMobileControlAction) => {
  if (action.type === 'keypress') {
    dispatchKey(action)
    return
  }
  const ok = action.type === 'click' ? clickBySelectors(action.selectors) : runCommand(action)
  showControlNotice(ok ? `已执行：${action.label}` : '当前步骤暂不可用')
}

onMounted(() => window.addEventListener('message', handleMessage))
onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
  if (noticeTimer !== null) window.clearTimeout(noticeTimer)
})
</script>

<template>
  <div class="fixed inset-0 z-[80] flex flex-col bg-slate-950">
    <header class="flex shrink-0 items-center justify-between border-b border-white/10 bg-slate-950/95 px-4 py-3 text-white backdrop-blur">
      <div class="min-w-0">
        <p class="text-xs text-white/50">Neuropsych Assessment</p>
        <h2 class="truncate text-base font-bold">{{ record.test_title || '神经心理测评' }}</h2>
      </div>
      <div class="flex items-center gap-3">
        <div v-if="submitting || received" class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs text-white/80">
          <Loader2 class="h-3.5 w-3.5 animate-spin" />
          正在保存结果
        </div>
        <button class="grid h-10 w-10 place-items-center rounded-full bg-white/10 transition hover:bg-white/20" type="button" @click="emit('close')">
          <X class="h-5 w-5" />
        </button>
      </div>
    </header>
    <main class="min-h-0 flex-1 bg-white">
      <iframe
        ref="iframeRef"
        :src="sourceUrl"
        :title="record.test_title || '神经心理测评'"
        class="h-full w-full border-0"
        allowfullscreen
      />
    </main>
    <div v-if="controlNotice" class="fixed bottom-[170px] left-1/2 z-[90] -translate-x-1/2 rounded-full bg-slate-950/90 px-4 py-2 text-xs font-bold text-white shadow-lg md:hidden">
      {{ controlNotice }}
    </div>
    <NeuropsychMobileControls :record="record" :disabled="Boolean(submitting || received)" @trigger="triggerMobileAction" />
  </div>
</template>
