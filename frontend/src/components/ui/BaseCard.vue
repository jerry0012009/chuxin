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
  <div :class="['service-card', padded ? 'p-4 md:p-5' : '', $props.class]">
    <slot />
  </div>
</template>
