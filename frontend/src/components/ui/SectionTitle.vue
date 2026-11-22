<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
  description?: string
}>()
</script>

<template>
  <div class="flex items-end justify-between gap-4">
    <div>
      <p v-if="eyebrow" class="mb-1 text-xs font-semibold uppercase tracking-[0.12em] text-primary/70">
        {{ eyebrow }}
      </p>
      <h2 class="text-xl font-bold text-slate-900 dark:text-white md:text-2xl">{{ title }}</h2>
      <p v-if="description" class="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {{ description }}
      </p>
    </div>
    <slot name="right" />
  </div>
</template>
