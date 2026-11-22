<script setup lang="ts">
withDefaults(
  defineProps<{
    padded?: boolean
    class?: string
  }>(),
  {
    padded: true,
    class: '',
  },
)
</script>

<template>
  <div :class="['soft-panel', padded ? 'p-5 md:p-6' : '', $props.class]">
    <slot />
  </div>
</template>
