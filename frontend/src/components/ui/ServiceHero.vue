<script setup lang="ts">
import { palaceImage } from '@/lib/service-preview'

defineProps<{ variant: 'full' | 'compact' | 'quiet'; title?: string; eyebrow?: string }>()
</script>

<template>
  <header class="service-hero" :class="`service-hero--${variant}`">
    <div class="service-width service-hero-inner">
      <img class="service-palace" :src="palaceImage" alt="" width="1200" height="524" />
      <div class="service-hero-copy">
        <p v-if="eyebrow" class="service-kicker">{{ eyebrow }}</p>
        <component :is="variant === 'full' ? 'h1' : 'p'" v-if="title" class="service-hero-title">{{ title }}</component>
        <slot />
      </div>
    </div>
  </header>
</template>
