<script setup lang="ts">
defineProps<{
  value: number
  tone?: string
}>()
</script>

<template>
  <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
    <div
      class="h-full rounded-full bg-gradient-to-r from-primary to-info transition-all duration-500"
      :class="tone"
      :style="{ width: `${Math.max(0, Math.min(100, value))}%` }"
    />
  </div>
</template>
