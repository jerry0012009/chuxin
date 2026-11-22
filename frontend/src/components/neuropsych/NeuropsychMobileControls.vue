<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeftRight, Check, CornerDownLeft, Hand, Layers, MousePointer2, TimerReset, Zap } from 'lucide-vue-next'
import type { NeuropsychMobileControlAction, NeuropsychMobileControlTone, NeuropsychRecord } from '@/types'

const props = defineProps<{
  record: NeuropsychRecord
  disabled?: boolean
}>()

const emit = defineEmits<{
  trigger: [NeuropsychMobileControlAction]
}>()

const iconMap = {
  ArrowLeftRight,
  Check,
  CornerDownLeft,
  Hand,
  Layers,
  MousePointer2,
  TimerReset,
  Zap,
}

const fallbackControls = (code?: string): NeuropsychMobileControlAction[] => {
  if (code?.includes('discount-titrate')) {
    return [
      { id: 'continue', label: '开始/继续', helper: '进入下一步', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'secondary' },
      { id: 'choose-left', label: '选左侧', helper: '按 Q', icon: 'ArrowLeftRight', type: 'keypress', key: 'q', code: 'KeyQ', keyCode: 81, tone: 'primary' },
      { id: 'choose-right', label: '选右侧', helper: '按 P', icon: 'ArrowLeftRight', type: 'keypress', key: 'p', code: 'KeyP', keyCode: 80, tone: 'success' },
    ]
  }
  if (code?.includes('columbia-card-task-hot')) {
    return [
      { id: 'continue', label: '回车/继续', helper: '说明和过渡页', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'primary' },
    ]
  }
  if (code?.includes('stroop')) {
    return [
      { id: 'continue', label: '开始/继续', helper: '说明页', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'secondary' },
      { id: 'red', label: '红', helper: '按 R', icon: 'Zap', type: 'keypress', key: 'r', code: 'KeyR', keyCode: 82, tone: 'danger' },
      { id: 'blue', label: '蓝', helper: '按 B', icon: 'Zap', type: 'keypress', key: 'b', code: 'KeyB', keyCode: 66, tone: 'primary' },
      { id: 'green', label: '绿', helper: '按 G', icon: 'Zap', type: 'keypress', key: 'g', code: 'KeyG', keyCode: 71, tone: 'success' },
    ]
  }
  if (code?.includes('flanker')) {
    return [
      { id: 'continue', label: '开始/继续', helper: '说明页', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'secondary' },
      { id: 'f', label: 'F', helper: '中间字母 F', icon: 'Zap', type: 'keypress', key: 'f', code: 'KeyF', keyCode: 70, tone: 'primary' },
      { id: 'h', label: 'H', helper: '中间字母 H', icon: 'Zap', type: 'keypress', key: 'h', code: 'KeyH', keyCode: 72, tone: 'success' },
    ]
  }
  if (code?.includes('emotion-regulation')) {
    return [
      { id: 'continue', label: '开始/继续', helper: '说明页', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'secondary' },
      { id: 'choose-left', label: '选左侧', helper: '按 ←', icon: 'ArrowLeftRight', type: 'keypress', key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, tone: 'primary' },
      { id: 'choose-right', label: '选右侧', helper: '按 →', icon: 'ArrowLeftRight', type: 'keypress', key: 'ArrowRight', code: 'ArrowRight', keyCode: 39, tone: 'success' },
    ]
  }
  if (code?.includes('digit-span')) {
    return [
      { id: 'continue', label: '开始/继续', helper: '说明和提交', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'primary' },
    ]
  }
  return [
    { id: 'continue', label: '开始/继续', helper: '说明页', icon: 'CornerDownLeft', type: 'command', command: 'advance', key: 'Enter', code: 'Enter', keyCode: 13, tone: 'secondary' },
    { id: 'respond', label: '反应', helper: 'Go 刺激时点击', icon: 'Zap', type: 'keypress', key: ' ', code: 'Space', keyCode: 32, tone: 'primary' },
  ]
}

const controls = computed(() => {
  const configured = props.record.config_json?.mobileControls
  return Array.isArray(configured) && configured.length ? configured : fallbackControls(props.record.test_code)
})

const primaryControls = computed(() => controls.value.filter((item) => item.tone && item.tone !== 'secondary'))
const secondaryControls = computed(() => controls.value.filter((item) => !item.tone || item.tone === 'secondary'))

const iconFor = (name?: string) => iconMap[(name || 'MousePointer2') as keyof typeof iconMap] || MousePointer2

const buttonClass = (tone: NeuropsychMobileControlTone = 'secondary', primary = false) => {
  const base = primary
    ? 'min-h-[58px] flex-1 rounded-[18px] px-3 py-2 text-sm font-black shadow-lg active:scale-[0.98]'
    : 'min-h-[42px] rounded-[14px] px-2.5 py-1.5 text-xs font-bold active:scale-[0.98]'
  const color = {
    primary: 'bg-blue-600 text-white shadow-blue-900/25',
    success: 'bg-emerald-600 text-white shadow-emerald-900/20',
    warning: 'bg-amber-500 text-slate-950 shadow-amber-900/20',
    danger: 'bg-rose-600 text-white shadow-rose-900/20',
    secondary: 'bg-white/10 text-white ring-1 ring-white/15',
  }[tone]
  return `${base} ${color} inline-flex items-center justify-center gap-2 transition disabled:opacity-45`
}
</script>

<template>
  <div class="shrink-0 bg-slate-950 px-3 pb-[calc(env(safe-area-inset-bottom)+8px)] pt-1.5 md:hidden">
    <div class="rounded-[20px] border border-white/10 bg-slate-950 p-2.5 text-white shadow-2xl shadow-slate-950/35">
      <div class="mb-2 flex items-center justify-between gap-3 px-1">
        <div>
          <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">Touch Console</p>
          <p class="text-xs font-bold text-white/80">移动端快捷操作</p>
        </div>
        <p class="max-w-[46%] text-right text-[10px] leading-3 text-white/45">映射实验按键或点击</p>
      </div>

      <div v-if="primaryControls.length" class="flex gap-2">
        <button
          v-for="control in primaryControls"
          :key="control.id"
          :class="buttonClass(control.tone, true)"
          :disabled="disabled"
          type="button"
          @click="emit('trigger', control)"
        >
          <component :is="iconFor(control.icon)" class="h-5 w-5 shrink-0" />
          <span class="min-w-0">
            <span class="block leading-5">{{ control.label }}</span>
            <span v-if="control.helper" class="block text-[10px] font-semibold opacity-70">{{ control.helper }}</span>
          </span>
        </button>
      </div>

      <div v-if="secondaryControls.length" class="mt-2 grid gap-2" :class="secondaryControls.length > 2 ? 'grid-cols-3' : 'grid-cols-2'">
        <button
          v-for="control in secondaryControls"
          :key="control.id"
          :class="buttonClass(control.tone)"
          :disabled="disabled"
          type="button"
          @click="emit('trigger', control)"
        >
          <component :is="iconFor(control.icon)" class="h-4 w-4 shrink-0" />
          <span class="min-w-0 truncate">{{ control.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
