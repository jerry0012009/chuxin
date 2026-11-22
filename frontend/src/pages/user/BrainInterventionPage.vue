<script setup lang="ts">
import { Activity, BrainCircuit, CheckCircle2, ChevronLeft, Clock, Loader2, Radio, Sparkles, SunMedium, Waves } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BiosignalMeditationDemo from '@/components/neurofeedback/BiosignalMeditationDemo.vue'
import WebEegNeurofeedbackDemo from '@/components/neurofeedback/WebEegNeurofeedbackDemo.vue'
import RealtimeSignalPanel from '@/components/sensors/RealtimeSignalPanel.vue'
import { completeInterventionItem, startInterventionItem } from '@/db/api'

const route = useRoute()
const router = useRouter()
const completing = ref(false)
const completed = ref(false)
const errorMessage = ref('')
const remaining = ref(10)
let timer: number | null = null

const modes = {
  light: {
    title: '光调控',
    subtitle: '通过节律化光刺激进行模拟训练',
    icon: SunMedium,
    tone: 'from-amber-400 to-orange-500',
    description: '当前为脑机干预预留模块，先用于记录管理员分配的模拟完成状态。真实设备接入上线后，这里会切换为设备连接与参数确认流程。',
  },
  magnetic: {
    title: '磁调控',
    subtitle: '模拟磁调控干预记录',
    icon: Radio,
    tone: 'from-cyan-400 to-blue-500',
    description: '当前不会触发真实设备，仅用于完成任务闭环和记录随访依从性。',
  },
  bci: {
    title: '脑机接口调控',
    subtitle: '脑机接口训练预留入口',
    icon: BrainCircuit,
    tone: 'from-emerald-400 to-teal-500',
    description: '后续可接入脑机接口设备、训练范式和数据回传；本期先以倒计时确认完成。',
  },
  neurofeedback: {
    title: '神经反馈训练',
    subtitle: 'Web EEG Neurofeedback Training',
    icon: BrainCircuit,
    tone: 'from-cyan-400 to-blue-500',
    description: '使用轻量特征流模拟神经反馈训练流程，结束后生成训练报告，后续可替换为真实 EEG 特征流。',
  },
  meditation: {
    title: '脑机交互冥想',
    subtitle: '视频引导 + EEG/心率/皮肤电监测',
    icon: Sparkles,
    tone: 'from-teal-400 to-emerald-500',
    description: '选择系统已有冥想视频后开始练习，同步读取网关中的 EEG、心率和皮肤电状态，结束后生成轻量训练报告。',
  },
  signals: {
    title: '实时生理信号',
    subtitle: 'EEG / 心率 / 皮肤电实时监测',
    icon: Activity,
    tone: 'from-teal-400 to-cyan-500',
    description: '通过 sensor gateway 查看 EEG、心率和皮肤电实时信号。当前 gateway 可由 CSV mock 数据或真实 BLE 硬件提供同一套 WS 数据协议。',
  },
}

const modeKey = computed(() => {
  const value = String(route.params.mode || 'signals')
  return value in modes ? value as keyof typeof modes : 'signals'
})
const mode = computed(() => modes[modeKey.value])
const recordId = computed(() => String(route.query.interventionRecordId || ''))
const returnTo = computed(() => String(route.query.returnTo || '/assessment-tasks'))
const canComplete = computed(() => remaining.value <= 0)
const isMeditationMode = computed(() => modeKey.value === 'meditation')
const isNeurofeedbackMode = computed(() => modeKey.value === 'neurofeedback')
const isSignalsMode = computed(() => modeKey.value === 'signals')

const clearTimer = () => {
  if (timer !== null) {
    window.clearInterval(timer)
    timer = null
  }
}

const startTimer = () => {
  clearTimer()
  remaining.value = Math.max(1, Number(route.query.duration || 10))
  timer = window.setInterval(() => {
    remaining.value -= 1
    if (remaining.value <= 0) clearTimer()
  }, 1000)
}

const completeTask = async () => {
  if (!recordId.value) {
    completed.value = true
    return
  }
  completing.value = true
  errorMessage.value = ''
  try {
    await completeInterventionItem(recordId.value, {
      source_ref_table: 'brain_intervention_simulation',
      source_ref_id: modeKey.value,
      duration_seconds: Math.max(10, Number(route.query.duration || 10)),
      summary_json: {
        mode: modeKey.value,
        title: mode.value.title,
      },
    })
    completed.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '记录脑机干预完成失败'
  } finally {
    completing.value = false
  }
}

onMounted(() => {
  if (recordId.value) void startInterventionItem(recordId.value).catch(() => {})
  startTimer()
})

watch(modeKey, startTimer)

onBeforeUnmount(clearTimer)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/40 pb-24 dark:from-slate-950 dark:via-slate-900 dark:to-cyan-950/20">
    <div class="sticky top-0 z-20 border-b border-slate-100 bg-white/85 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/85">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <button class="inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" type="button" @click="router.push(returnTo)">
          <ChevronLeft class="h-4 w-4" />
          返回任务
        </button>
        <span class="rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200">模拟记录</span>
      </div>
    </div>

    <main class="mx-auto max-w-5xl space-y-6 px-4 pt-6">
      <section class="overflow-hidden rounded-[32px] border border-white bg-white shadow-xl shadow-cyan-100/50 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none">
        <div :class="['bg-gradient-to-br p-6 text-white', mode.tone]">
          <div class="flex items-start justify-between gap-4">
            <div>
              <div class="inline-flex items-center gap-2 rounded-full bg-white/20 px-3 py-1 text-xs font-bold backdrop-blur">
                <Waves class="h-4 w-4" />
                脑机干预
              </div>
              <h1 class="mt-5 text-3xl font-black">{{ mode.title }}</h1>
              <p class="mt-2 text-sm leading-7 text-white/85">{{ mode.subtitle }}</p>
            </div>
            <div class="grid h-16 w-16 place-items-center rounded-3xl bg-white/20 backdrop-blur">
              <component :is="mode.icon" class="h-8 w-8" />
            </div>
          </div>
        </div>

        <div class="grid gap-6 p-6 md:grid-cols-[1fr_280px]">
          <div class="space-y-5">
            <div class="rounded-[24px] bg-slate-50 p-5 dark:bg-slate-950">
              <p class="text-sm leading-7 text-slate-600 dark:text-slate-300">{{ mode.description }}</p>
            </div>
            <div class="grid gap-3 sm:grid-cols-3">
              <router-link v-for="(item, key) in modes" :key="key" :to="{ path: `/brain-intervention/${key}`, query: route.query }" class="rounded-2xl border p-4 text-sm font-bold transition" :class="modeKey === key ? 'border-cyan-300 bg-cyan-50 text-cyan-700' : 'border-slate-100 bg-slate-50 text-slate-500 dark:border-slate-800 dark:bg-slate-950'">
                {{ item.title }}
              </router-link>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <button class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 hover:border-cyan-300 hover:text-cyan-700 dark:border-slate-700 dark:text-slate-200" type="button" @click="router.push('/brain-intervention/reports')">
                <Clock class="h-4 w-4" />
                查看训练报告
              </button>
            </div>
            <div v-if="errorMessage" class="rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-600 dark:bg-rose-950/30 dark:text-rose-200">{{ errorMessage }}</div>
          </div>

          <div class="rounded-[28px] border border-slate-100 bg-slate-50 p-5 text-center dark:border-slate-800 dark:bg-slate-950">
            <div class="mx-auto grid h-20 w-20 place-items-center rounded-full bg-white text-cyan-600 shadow-sm dark:bg-slate-900">
              <CheckCircle2 v-if="completed" class="h-10 w-10 text-emerald-500" />
              <Clock v-else class="h-10 w-10" />
            </div>
            <p class="mt-4 text-sm font-bold text-slate-500">{{ completed ? '今日已完成' : '倒计时完成后可记录' }}</p>
            <p class="mt-2 text-4xl font-black text-slate-900 dark:text-white">{{ completed ? 'OK' : remaining }}</p>
            <button
              class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-black transition"
              :class="canComplete || completed ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-200 text-slate-400 dark:bg-slate-800'"
              :disabled="(!canComplete && !completed) || completing"
              type="button"
              @click="completed ? router.push(returnTo) : completeTask()"
            >
              <Loader2 v-if="completing" class="h-4 w-4 animate-spin" />
              <Sparkles v-else class="h-4 w-4" />
              {{ completed ? '返回任务中心' : canComplete ? '记录完成' : '请稍候' }}
            </button>
          </div>
        </div>
      </section>

      <BiosignalMeditationDemo v-if="isMeditationMode" />
      <WebEegNeurofeedbackDemo v-else-if="isNeurofeedbackMode" />
      <RealtimeSignalPanel v-else-if="isSignalsMode" />
    </main>
  </div>
</template>
