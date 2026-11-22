<script setup lang="ts">
import {
  ArrowRight,
  Check,
  ChevronLeft,
  CreditCard,
  Crown,
  History,
  Receipt,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-vue-next'
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

interface Plan {
  id: 'monthly' | 'yearly' | 'lifetime'
  name: string
  price: string
  originalPrice?: string
  tag: string
  popular?: boolean
  features: string[]
}

const router = useRouter()
const selectedPlan = ref<Plan['id']>('yearly')
const statusMessage = ref('')
let subscribeTimer: number | null = null
let clearStatusTimer: number | null = null

const plans: Plan[] = [
  {
    id: 'monthly',
    name: '月度会员',
    price: '¥28',
    originalPrice: '¥45',
    tag: '入门首选',
    features: ['多模态AI情绪分析', '全量心理评估量表', '高清报告下载', '7x24小时AI陪伴'],
  },
  {
    id: 'yearly',
    name: '年度会员',
    price: '¥198',
    originalPrice: '¥540',
    tag: '超值推荐',
    popular: true,
    features: ['包含月度所有权益', '专家1对1咨询折扣', '高级冥想课程解锁', '专属身份标识'],
  },
  {
    id: 'lifetime',
    name: '终身会员',
    price: '¥698',
    tag: '一劳永逸',
    features: ['终身解锁所有功能', '未来所有高级权益', '限量定制周边', '终身云端存储'],
  },
]

const managementItems = [
  { label: '历史记录', icon: History, tone: 'bg-indigo-50 text-indigo-500' },
  { label: '申请发票', icon: Receipt, tone: 'bg-rose-50 text-rose-500' },
  { label: '续费管理', icon: ShieldCheck, tone: 'bg-emerald-50 text-emerald-500' },
]

const handleSubscribe = () => {
  if (subscribeTimer !== null) window.clearTimeout(subscribeTimer)
  if (clearStatusTimer !== null) window.clearTimeout(clearStatusTimer)
  statusMessage.value = '正在调起支付模块...'
  subscribeTimer = window.setTimeout(() => {
    statusMessage.value = '支付环境安全，请在弹出的窗口中完成支付'
    clearStatusTimer = window.setTimeout(() => {
      statusMessage.value = ''
    }, 2500)
  }, 1500)
}

onBeforeUnmount(() => {
  if (subscribeTimer !== null) window.clearTimeout(subscribeTimer)
  if (clearStatusTimer !== null) window.clearTimeout(clearStatusTimer)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 pb-20 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
    <div
      v-if="statusMessage"
      class="fixed left-1/2 top-[72px] z-[70] -translate-x-1/2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-xl shadow-slate-900/20"
      data-testid="subscription-toast"
    >
      {{ statusMessage }}
    </div>
    <div class="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 px-4 pb-16 pt-4">
      <Crown class="absolute right-8 top-0 h-40 w-40 rotate-12 text-white opacity-10" />
      <div class="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-white/10 blur-3xl" />
      <div class="absolute right-1/3 top-10 h-20 w-20 rounded-full bg-white/10 blur-2xl" />

      <div class="relative z-10 flex items-center gap-4 text-white">
        <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-white/20" @click="router.back()">
          <ChevronLeft class="h-6 w-6" />
        </button>
        <h1 class="text-xl font-bold">会员中心</h1>
      </div>

      <div class="relative z-10 mt-6 px-2">
        <div class="flex items-center gap-4 rounded-3xl border border-white/20 bg-white/10 p-5 text-white backdrop-blur-xl">
          <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-orange-500/30">
            <Crown class="h-7 w-7" />
          </div>
          <div class="flex-1">
            <div class="mb-1 flex items-center gap-2">
              <span class="text-lg font-bold">普通会员</span>
              <span class="rounded-full border border-white/30 bg-white/20 px-2 py-0.5 text-[10px] backdrop-blur-sm">未开通</span>
            </div>
            <p class="text-xs text-white/80">开通会员，解锁 12 项高级 AI 疗愈权益</p>
          </div>
          <Sparkles class="h-6 w-6 text-amber-300" />
        </div>
      </div>
    </div>

    <main class="relative z-20 mx-auto -mt-10 max-w-2xl space-y-6 p-4">
      <div class="space-y-3">
        <button
          v-for="plan in plans"
          :key="plan.id"
          class="w-full overflow-hidden rounded-2xl border-2 bg-white text-left shadow-md transition hover:shadow-lg dark:bg-slate-900"
          :class="selectedPlan === plan.id ? 'scale-[1.02] border-purple-500 bg-gradient-to-br from-purple-50/60 to-pink-50/60 shadow-xl shadow-purple-500/20' : 'border-slate-200/60 hover:border-purple-200 dark:border-slate-800'"
          data-testid="subscription-plan"
          @click="selectedPlan = plan.id"
        >
          <div v-if="plan.popular" class="bg-gradient-to-r from-purple-500 to-pink-500 py-1.5 text-center text-[10px] font-bold uppercase tracking-widest text-white">
            <Sparkles class="mr-1 inline-block h-3 w-3" />
            最受欢迎
          </div>
          <div class="p-5">
            <div class="mb-3 flex items-center justify-between gap-4">
              <div class="flex items-center gap-4">
                <div
                  class="flex h-12 w-12 items-center justify-center rounded-2xl"
                  :class="selectedPlan === plan.id ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white' : 'bg-slate-100 text-purple-500'"
                >
                  <Zap v-if="plan.id === 'lifetime'" class="h-6 w-6" />
                  <CreditCard v-else class="h-6 w-6" />
                </div>
                <div>
                  <div class="text-lg font-bold text-slate-900 dark:text-white">{{ plan.name }}</div>
                  <span class="mt-1 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">{{ plan.tag }}</span>
                </div>
              </div>
              <div class="text-right">
                <div class="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-2xl font-black text-transparent">{{ plan.price }}</div>
                <div v-if="plan.originalPrice" class="text-xs text-slate-400 line-through">{{ plan.originalPrice }}</div>
              </div>
            </div>

            <div class="flex flex-wrap gap-2 border-t pt-3" :class="selectedPlan === plan.id ? 'border-purple-200' : 'border-slate-100 dark:border-slate-800'">
              <div v-for="feature in plan.features" :key="feature" class="flex items-center gap-1 text-[11px] text-slate-600 dark:text-slate-300">
                <span class="flex h-4 w-4 items-center justify-center rounded-full" :class="selectedPlan === plan.id ? 'bg-purple-100 text-purple-500' : 'bg-slate-100 text-slate-500'">
                  <Check class="h-2.5 w-2.5" />
                </span>
                {{ feature }}
              </div>
            </div>
          </div>
        </button>
      </div>

      <section class="overflow-hidden rounded-2xl bg-white shadow-lg dark:bg-slate-900">
        <div class="bg-gradient-to-r from-slate-50 to-white px-5 py-4 dark:from-slate-900 dark:to-slate-900">
          <h2 class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-200">
            <ShieldCheck class="h-4 w-4 text-emerald-500" />
            安全支付环境
          </h2>
        </div>
        <div class="grid grid-cols-3 gap-3 p-4">
          <button class="flex flex-col items-center gap-2 rounded-xl border-2 border-blue-100 bg-blue-50/50 p-3 transition hover:border-blue-300">
            <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-bold text-white shadow-lg shadow-blue-500/30">支</span>
            <span class="text-[11px] font-semibold text-slate-700">支付宝</span>
          </button>
          <button class="flex flex-col items-center gap-2 rounded-xl border-2 border-emerald-100 bg-emerald-50/50 p-3 transition hover:border-emerald-300">
            <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 text-sm font-bold text-white shadow-lg shadow-emerald-500/30">微</span>
            <span class="text-[11px] font-semibold text-slate-700">微信支付</span>
          </button>
          <button class="flex flex-col items-center gap-2 rounded-xl border-2 border-slate-200 bg-slate-50/50 p-3 transition hover:border-slate-400">
            <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-800 text-white shadow-lg shadow-slate-500/30">
              <CreditCard class="h-5 w-5" />
            </span>
            <span class="text-[11px] font-semibold text-slate-700">信用卡</span>
          </button>
        </div>
      </section>

      <div class="grid grid-cols-3 gap-3">
        <button v-for="item in managementItems" :key="item.label" class="flex flex-col items-center gap-2 rounded-2xl border border-slate-100 bg-white p-4 shadow-md transition hover:shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl" :class="item.tone">
            <component :is="item.icon" class="h-5 w-5" />
          </span>
          <span class="text-[11px] font-medium text-slate-600 dark:text-slate-300">{{ item.label }}</span>
        </button>
      </div>

      <div>
        <button
          class="flex h-14 w-full items-center justify-center rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-lg font-bold text-white shadow-2xl shadow-purple-500/30 transition hover:scale-[1.02] active:scale-[0.98]"
          data-testid="subscription-submit"
          @click="handleSubscribe"
        >
          <Crown class="mr-2 h-5 w-5" />
          立即开通会员
          <ArrowRight class="ml-2 h-5 w-5" />
        </button>
        <p class="mt-3 text-center text-[10px] text-slate-400">开通即表示同意《会员服务协议》</p>
      </div>
    </main>
  </div>
</template>
