<script setup lang="ts">
import { ShieldCheck } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { systemName } from '@/lib/service-preview'

withDefaults(defineProps<{ caption?: string; home?: string }>(), { caption: '身心健康服务' })
</script>

<template>
  <header class="service-masthead">
    <div class="service-width service-brand">
      <component :is="home ? RouterLink : 'div'" :to="home" class="service-brand-link">
        <span class="service-brand-mark"><ShieldCheck :size="25" aria-hidden="true" /></span>
        <div><p class="service-brand-title">{{ systemName }}</p><p class="service-brand-caption">{{ caption }}</p></div>
      </component>
      <span class="service-preview-label">方案预览</span>
    </div>
  </header>
</template>
