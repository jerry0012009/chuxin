<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info } from 'lucide-vue-next'
import type { NeuropsychFeedbackCard, NeuropsychWarningLevel } from '@/types'

defineProps<{
  card: NeuropsychFeedbackCard
}>()

const levelClass = (level?: NeuropsychWarningLevel) => {
  if (level === 'high') return 'bg-rose-500 text-white'
  if (level === 'middle') return 'bg-amber-500 text-white'
  if (level === 'low') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200'
  return 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-200'
}

const levelIcon = (level?: NeuropsychWarningLevel) => {
  if (level === 'high' || level === 'middle') return AlertTriangle
  if (level === 'low') return Info
  return CheckCircle2
}
</script>

<template>
  <article class="rounded-[24px] border border-slate-100 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-xs font-semibold text-slate-400">{{ card.subtitle || '测评反馈' }}</p>
        <h3 class="mt-1 text-lg font-black text-slate-900 dark:text-white">{{ card.title }}</h3>
      </div>
      <span :class="['inline-flex shrink-0 items-center gap-1 rounded-full px-3 py-1 text-xs font-bold', levelClass(card.level)]">
        <component :is="levelIcon(card.level)" class="h-3.5 w-3.5" />
        {{ card.primaryValue || '结果反馈' }}
      </span>
    </div>

    <div v-if="card.items?.length" class="mt-5 grid gap-3 sm:grid-cols-2">
      <div v-for="item in card.items" :key="item.label" class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
        <p class="text-xs text-slate-400">{{ item.label }}</p>
        <p class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ item.value }}</p>
      </div>
    </div>

    <p v-if="card.conclusion" class="mt-5 text-sm leading-7 text-slate-700 dark:text-slate-300">{{ card.conclusion }}</p>
    <p v-if="card.suggestion" class="mt-3 rounded-2xl bg-blue-50 p-4 text-sm leading-7 text-blue-700 dark:bg-blue-950/30 dark:text-blue-200">
      {{ card.suggestion }}
    </p>
  </article>
</template>
