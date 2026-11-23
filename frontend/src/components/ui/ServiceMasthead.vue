<script setup lang="ts">
import { ShieldCheck } from 'lucide-vue-next'
import { systemName } from '@/lib/service-preview'
</script>

<template>
  <header class="service-masthead">
    <div class="service-width service-brand">
      <span class="service-brand-mark"><ShieldCheck :size="25" aria-hidden="true" /></span>
      <div><p class="service-brand-title">{{ systemName }}</p><p class="service-brand-caption">身心健康服务</p></div>
      <span class="service-preview-label">方案预览</span>
    </div>
  </header>
</template>
