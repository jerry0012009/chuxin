<script setup lang="ts">
defineProps<{
  value: number
  tone?: string
  label?: string
}>()
</script>

<template>
  <progress class="service-progress block" max="100" :value="Math.max(0, Math.min(100, value))" :aria-label="label || '完成进度'" />
</template>
