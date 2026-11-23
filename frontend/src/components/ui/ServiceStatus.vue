<script setup lang="ts">
withDefaults(defineProps<{ tone?: 'active' | 'idle' | 'done' | 'attention' | 'danger' }>(), { tone: 'idle' })
</script>

<template>
  <span class="service-status" :class="`service-status-${tone}`"><slot /></span>
</template>
