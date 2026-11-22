<script setup lang="ts">
import {
  ChevronRight,
  Flower2,
  Gamepad2,
  Heart,
  MessageCircle,
  Moon,
  Music,
  Palette,
  ShieldCheck,
  Sparkles,
  Wind,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getEmotionDiaries, getMyAssessmentPublishTasks } from '@/db/api'
import { useAuthSession } from '@/composables/useAuthSession'

const router = useRouter()
const { state: authState } = useAuthSession()

type NavigationState = Record<string, string | number | boolean | null | undefined>

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const encouragement = ref(
  [
    '🌿 今天也要好好爱自己哦',
    '🌟 每一天都是崭新的开始',
    '💖 你值得拥有美好的一切',
    '🌈 生活充满希望，一起加油',
    '✨ 每个早晨都是新的奇迹',
    '🌸 微笑面对生活，温暖常在',
  ][Math.floor(Math.random() * 6)],
)

const mainFeatures = [
  {
    title: 'AI多模态评估',
    subtitle: '每日可测',
    desc: '完成心理状态综合观察',
    icon: Sparkles,
    gradient: 'from-rose-300 via-pink-400 to-purple-400',
    shadow: 'shadow-rose-200',
    path: '/assessment',
  },
  {
    title: '记录心情',
    subtitle: '情绪日记',
    desc: '记录每一天的感受',
    icon: Heart,
    gradient: 'from-orange-300 via-amber-300 to-yellow-300',
    shadow: 'shadow-orange-200',
    path: '/record',
  },
  {
    title: '放松疗愈',
    subtitle: '冥想空间',
    desc: '找到内心的宁静',
    icon: Flower2,
    gradient: 'from-teal-300 via-emerald-300 to-green-300',
    shadow: 'shadow-teal-200',
    path: '/healing',
  },
]

const primaryFeature = mainFeatures[0]!

const quickActions = [
  {
    title: '多模态',
    icon: MessageCircle,
    color: 'bg-violet-100 text-violet-600',
    path: '/assessment',
    state: undefined,
  },
  {
    title: '睡眠',
    icon: Moon,
    color: 'bg-indigo-100 text-indigo-600',
    path: '/healing',
    state: { activeTab: 'meditation', activeCategory: 'sleep' },
  },
  {
    title: '放松',
    icon: Wind,
    color: 'bg-sky-100 text-sky-600',
    path: '/healing',
    state: { activeTab: 'meditation', activeCategory: 'relax' },
  },
  {
    title: '音乐',
    icon: Music,
    color: 'bg-rose-100 text-rose-600',
    path: '/healing',
    state: { activeTab: 'meditation' },
  },
  {
    title: '更多',
    icon: Palette,
    color: 'bg-amber-100 text-amber-600',
    path: '/healing',
    state: undefined,
  },
] as const

const featuredContent = [
  {
    title: '焦虑缓解呼吸法',
    type: '放松',
    duration: '3分钟',
    image: '🌸',
    bgColor: 'from-pink-100 to-rose-100',
    trackIndex: 0,
  },
  {
    title: '睡前放松引导',
    type: '睡眠',
    duration: '15分钟',
    image: '🌙',
    bgColor: 'from-indigo-100 to-purple-100',
    trackIndex: 1,
  },
  {
    title: '身体扫描冥想',
    type: '放松',
    duration: '10分钟',
    image: '☀️',
    bgColor: 'from-amber-100 to-orange-100',
    trackIndex: 2,
  },
  {
    title: '专注力训练',
    type: '专注',
    duration: '8分钟',
    image: '🎯',
    bgColor: 'from-emerald-100 to-teal-100',
    trackIndex: 3,
  },
  {
    title: '抑郁症康复之路',
    type: '专注',
    duration: '12分钟',
    image: '🌈',
    bgColor: 'from-violet-100 to-purple-100',
    trackIndex: 4,
  },
]

const openPath = (path: string, state?: NavigationState) => {
  router.push(state ? { path, state } : path)
}

const warmName = computed(() => authState.profile?.full_name || '朋友')
const assessmentTasks = ref<any[]>([])
const defaultTask = computed(() => assessmentTasks.value.find((item) => item.status !== 'completed') || assessmentTasks.value[0] || null)
const taskItems = computed(() => defaultTask.value?.items || [])
const taskCompletedCount = computed(() => taskItems.value.filter((item: any) => item.status === 'completed' || item.status === 'unsupported').length)
const taskProgress = computed(() => (taskItems.value.length ? Math.round((taskCompletedCount.value / taskItems.value.length) * 100) : 0))

onMounted(async () => {
  if (!authState.user) return
  try {
    assessmentTasks.value = await getMyAssessmentPublishTasks()
  } catch {
    assessmentTasks.value = []
  }
})

if (authState.user) {
  void getEmotionDiaries(authState.user.id, 1).catch(() => {
    // Background warm-up only; record page and profile surface their own loading errors.
  })
}
</script>

<template>
  <div class="min-h-screen bg-[#FAFAFA] pb-24 dark:bg-slate-950 md:pb-0">
    <div class="relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-b from-rose-50/80 via-purple-50/50 to-transparent dark:from-slate-900 dark:via-slate-900/50" />
      <div class="absolute -top-20 right-0 h-72 w-72 rounded-full bg-gradient-to-br from-rose-200/40 to-pink-200/40 blur-3xl" />
      <div class="absolute -left-20 top-20 h-64 w-64 rounded-full bg-gradient-to-br from-violet-200/40 to-purple-200/40 blur-3xl" />

      <div class="page-grid relative z-10 pb-6 pt-8">
        <div class="mb-3">
          <p class="mb-0.5 text-sm text-slate-500 dark:text-slate-400">{{ greeting }}</p>
          <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100 md:text-3xl">
            {{ warmName }} ✨
          </h1>
        </div>
      </div>
    </div>

    <div class="page-grid space-y-6">
      <section v-if="defaultTask && defaultTask.status !== 'completed'">
        <button
          class="w-full overflow-hidden rounded-[28px] border border-cyan-100 bg-gradient-to-br from-cyan-50 via-white to-emerald-50 p-5 text-left text-slate-900 shadow-xl shadow-cyan-100/70 transition hover:-translate-y-0.5 dark:border-slate-800 dark:from-slate-900 dark:via-slate-950 dark:to-emerald-950/30 dark:text-white dark:shadow-none"
          type="button"
          @click="router.push(`/assessment-tasks/${defaultTask.id}`)"
        >
          <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div class="flex gap-4">
              <div class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-cyan-400/10 dark:text-cyan-200">
                <ShieldCheck class="h-6 w-6" />
              </div>
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.12em] text-cyan-700 dark:text-cyan-200">待完成测评任务</p>
                <h2 class="mt-1 text-xl font-black md:text-2xl">{{ defaultTask.batch_title || defaultTask.title || '职务犯罪风险与心理状态初筛' }}</h2>
                <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">按引导完成量表、神经心理、对话、语音和表情评估，完成后生成综合报告。</p>
              </div>
            </div>
            <div class="min-w-48 rounded-2xl bg-white/75 p-4 shadow-sm ring-1 ring-cyan-100 dark:bg-slate-900/70 dark:ring-slate-800">
              <div class="flex items-center justify-between text-sm">
                <span>进度</span>
                <span class="font-black">{{ taskCompletedCount }} / {{ taskItems.length || 5 }}</span>
              </div>
              <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div class="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400" :style="{ width: `${taskProgress}%` }" />
              </div>
              <p class="mt-3 text-xs font-bold text-cyan-700 dark:text-cyan-200">进入任务中心</p>
            </div>
          </div>
        </button>
      </section>

      <section>
        <div class="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4 lg:grid-cols-4 lg:gap-5">
          <button
            data-testid="home-feature-assessment"
            class="relative col-span-2 overflow-hidden rounded-3xl bg-gradient-to-br p-6 text-left shadow-lg transition hover:-translate-y-1 md:col-span-1 md:p-8 lg:col-span-2"
            :class="[primaryFeature.gradient, primaryFeature.shadow]"
            type="button"
            @click="router.push(primaryFeature.path)"
          >
            <div class="absolute right-0 top-0 h-40 w-40 translate-x-1/3 -translate-y-1/2 rounded-full bg-white/20" />
            <div class="relative z-10">
              <div class="mb-3 flex items-center gap-2">
                <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/30 backdrop-blur-sm md:h-12 md:w-12">
                  <Sparkles class="h-5 w-5 text-white md:h-6 md:w-6" />
                </div>
                <span class="rounded-full bg-white/30 px-2 py-1 text-[10px] text-white md:text-xs">
                  {{ primaryFeature.subtitle }}
                </span>
              </div>
              <h2 class="mb-1 text-xl font-bold text-white md:text-2xl">{{ primaryFeature.title }}</h2>
              <p class="text-sm text-white/80 md:text-base">{{ primaryFeature.desc }}</p>
            </div>
          </button>

          <button
            v-for="feature in mainFeatures.slice(1)"
            :key="feature.title"
            :data-testid="feature.path === '/record' ? 'home-feature-record' : 'home-feature-healing'"
            class="relative overflow-hidden rounded-2xl bg-gradient-to-br p-4 text-left shadow-lg transition hover:-translate-y-1 md:rounded-3xl md:p-6"
            :class="[feature.gradient, feature.shadow]"
            type="button"
            @click="router.push(feature.path)"
          >
            <div class="absolute -bottom-4 -right-4 h-20 w-20 rounded-full bg-white/20 md:h-32 md:w-32" />
            <div class="relative z-10">
              <div class="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white/30 backdrop-blur-sm md:h-12 md:w-12">
                <component :is="feature.icon" class="h-4 w-4 text-white md:h-6 md:w-6" />
              </div>
              <h3 class="mb-0.5 text-base font-bold text-white md:text-lg">{{ feature.title }}</h3>
              <p class="text-xs text-white/70 md:text-sm">{{ feature.desc }}</p>
            </div>
          </button>
        </div>
      </section>

      <section>
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100 md:text-xl">精选内容</h3>
          <button data-testid="home-featured-all" class="flex items-center gap-1 text-sm font-medium text-violet-600" type="button" @click="router.push('/healing')">
            全部
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>
      </section>

      <section class="-mt-2">
        <button
          data-testid="home-game-card"
          class="relative w-full cursor-pointer overflow-hidden rounded-3xl bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 p-5 text-left shadow-xl shadow-blue-200 transition hover:-translate-y-0.5 md:p-6"
          type="button"
          @click="openPath('/healing', { activeTab: 'game' })"
        >
          <div class="flex items-center justify-between gap-4">
            <div>
              <div class="mb-2 flex items-center gap-2">
                <Gamepad2 class="h-5 w-5 text-white md:h-6 md:w-6" />
                <span class="font-bold text-white md:text-lg">趣味疗愈游戏</span>
              </div>
              <p class="text-sm text-white/80 md:text-base">
                基于认知训练的趣味交互，释放压力并提升专注力
              </p>
            </div>
            <div class="flex -space-x-2">
              <div class="flex h-10 w-10 items-center justify-center rounded-full border-2 border-white/50 bg-white/30 text-lg md:h-12 md:w-12 md:text-xl">🎮</div>
              <div class="flex h-10 w-10 items-center justify-center rounded-full border-2 border-white/50 bg-white/30 text-lg md:h-12 md:w-12 md:text-xl">🧩</div>
              <div class="flex h-10 w-10 items-center justify-center rounded-full border-2 border-white/50 bg-white/30 text-lg md:h-12 md:w-12 md:text-xl">🚀</div>
            </div>
          </div>
        </button>
      </section>

      <section>
        <div class="-mx-5 overflow-x-auto px-5 scrollbar-hide md:mx-0 md:px-0">
          <div class="flex gap-3 pb-2 md:gap-4 lg:grid lg:grid-cols-5 lg:gap-5">
            <button
              v-for="item in featuredContent"
              :key="item.title"
              data-testid="home-featured-content"
              class="w-[140px] flex-none cursor-pointer overflow-hidden rounded-2xl bg-white text-left shadow-lg shadow-slate-200/50 transition hover:-translate-y-1 md:w-[180px] md:rounded-3xl lg:w-auto dark:bg-slate-800"
              type="button"
              @click="openPath('/healing', { activeTab: 'meditation', trackIndex: item.trackIndex })"
            >
              <div class="relative flex h-24 items-center justify-center bg-gradient-to-br text-4xl md:h-32 md:text-5xl" :class="item.bgColor">
                {{ item.image }}
              </div>
              <div class="p-3 md:p-4">
                <p class="mb-1 text-[10px] text-slate-400 md:text-xs">{{ item.type }} · {{ item.duration }}</p>
                <h4 class="line-clamp-2 text-sm font-bold leading-tight text-slate-800 dark:text-slate-100 md:text-base">
                  {{ item.title }}
                </h4>
              </div>
            </button>
          </div>
        </div>
      </section>

      <section>
        <div class="flex justify-between md:justify-center md:gap-8">
          <button
            v-for="action in quickActions"
            :key="action.title"
            class="flex flex-col items-center gap-2 md:gap-3"
            type="button"
            @click="openPath(action.path, action.state)"
          >
            <div :class="['flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg md:h-16 md:w-16', action.color]">
              <component :is="action.icon" class="h-6 w-6 md:h-7 md:w-7" />
            </div>
            <span class="text-xs font-medium text-slate-600 dark:text-slate-400 md:text-sm">
              {{ action.title }}
            </span>
          </button>
        </div>
      </section>

      <section class="pb-6 text-center">
        <p class="text-sm text-slate-400 dark:text-slate-500">{{ encouragement }}</p>
      </section>
    </div>
  </div>
</template>
