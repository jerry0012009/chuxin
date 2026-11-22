<script setup lang="ts">
import {
  Award,
  Brain,
  Check,
  ChevronLeft,
  Heart,
  Mail,
  MessageSquare,
  Shield,
  Sparkles,
  Users,
  Zap,
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    icon: Sparkles,
    title: '多模态AI识别',
    desc: '融合语音、文本、表情多维度数据',
    color: 'from-indigo-500 to-purple-500',
    bg: 'bg-indigo-50 dark:bg-indigo-950/30',
  },
  {
    icon: Users,
    title: '专家管理员复核',
    desc: '专业管理员团队二次审核',
    color: 'from-rose-500 to-pink-500',
    bg: 'bg-rose-50 dark:bg-rose-950/30',
  },
  {
    icon: Heart,
    title: '个性化疗愈',
    desc: '定制专属康复计划和建议',
    color: 'from-teal-500 to-emerald-500',
    bg: 'bg-teal-50 dark:bg-teal-950/30',
  },
  {
    icon: Shield,
    title: '医学级隐私',
    desc: '端到端加密，保障数据安全',
    color: 'from-amber-500 to-orange-500',
    bg: 'bg-amber-50 dark:bg-amber-950/30',
  },
]

const highlights = [
  '三甲医院管理员团队支持',
  '符合HIPAA医疗数据隐私标准',
  '通过国家医疗器械二类认证',
  '已在全球多国上线服务',
]
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 pb-20 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
    <div class="sticky top-0 z-30 flex items-center gap-4 border-b border-slate-200/50 bg-white/80 px-4 py-4 backdrop-blur-xl dark:border-slate-800/50 dark:bg-slate-950/80">
      <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800" @click="router.back()">
        <ChevronLeft class="h-6 w-6 text-slate-700 dark:text-slate-200" />
      </button>
      <h1 class="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-lg font-bold text-transparent">关于我们</h1>
    </div>

    <main class="mx-auto max-w-md space-y-10 px-6 pt-6">
      <section class="relative overflow-hidden rounded-[32px] bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-8 shadow-2xl" data-testid="about-hero">
        <div class="absolute inset-0 overflow-hidden">
          <div class="absolute -right-20 -top-20 h-60 w-60 rounded-full bg-white/20 blur-3xl" />
          <div class="absolute -bottom-20 -left-20 h-60 w-60 rounded-full bg-white/20 blur-3xl" />
        </div>

        <div class="relative z-10 space-y-5 text-center">
          <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-[24px] border border-white/30 bg-white/20 shadow-xl backdrop-blur-lg">
            <Brain class="h-11 w-11 text-white" />
          </div>

          <div>
            <h2 class="mb-2 text-3xl font-black tracking-tight text-white">初心</h2>
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-white/90">数字化心理健康服务</p>
          </div>

          <p class="mx-auto max-w-[280px] text-sm leading-relaxed text-white/95">
            用多模态AI与人文关怀，打造专业、私密、温暖的心理健康服务。
          </p>

          <div class="flex flex-wrap justify-center gap-2 pt-2">
            <span class="rounded-full border border-white/40 bg-white/25 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">隐私加密</span>
            <span class="rounded-full border border-white/40 bg-white/25 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">医学规范</span>
            <span class="rounded-full border border-white/40 bg-white/25 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">全天候响应</span>
          </div>
        </div>
      </section>

      <section class="space-y-4">
        <div class="flex items-center gap-2">
          <Zap class="h-5 w-5 text-indigo-600" />
          <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">我们做什么</h3>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <article v-for="feature in features" :key="feature.title" class="rounded-2xl border-0 p-5 transition hover:shadow-lg" :class="feature.bg" data-testid="about-feature-card">
            <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br shadow-md" :class="feature.color">
              <component :is="feature.icon" class="h-6 w-6 text-white" />
            </div>
            <div class="mt-3">
              <h4 class="mb-1 text-sm font-bold text-slate-900 dark:text-slate-100">{{ feature.title }}</h4>
              <p class="text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">{{ feature.desc }}</p>
            </div>
          </article>
        </div>
      </section>

      <section class="space-y-4">
        <div class="flex items-center gap-2">
          <Award class="h-5 w-5 text-rose-600" />
          <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">专业认证</h3>
        </div>

        <div class="space-y-2.5 rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 p-5 shadow-md dark:from-rose-950/20 dark:to-pink-950/20" data-testid="about-certifications">
          <div v-for="text in highlights" :key="text" class="flex items-center gap-3">
            <div class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-rose-500 to-pink-500">
              <Check class="h-3 w-3 text-white" />
            </div>
            <p class="text-xs font-medium text-slate-700 dark:text-slate-300">{{ text }}</p>
          </div>
        </div>
      </section>

      <section class="space-y-4">
        <h3 class="text-center text-sm font-bold uppercase tracking-widest text-slate-400">联系我们</h3>
        <div class="flex justify-center gap-4">
          <button class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg transition hover:shadow-xl" data-testid="about-email">
            <Mail class="h-6 w-6 text-white" />
          </button>
          <button class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg transition hover:shadow-xl" data-testid="about-message">
            <MessageSquare class="h-6 w-6 text-white" />
          </button>
        </div>
      </section>

      <footer class="pb-2 pt-6 text-center">
        <p class="text-[11px] font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-600">
          Made with ❤️ for Mental Health
        </p>
        <p class="mt-2 text-[10px] font-medium text-slate-300 dark:text-slate-700">初心 v1.0.0</p>
      </footer>
    </main>
  </div>
</template>
