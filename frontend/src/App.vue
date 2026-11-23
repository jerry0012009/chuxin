<script setup lang="ts">
import { RouterView } from 'vue-router'
import { palaceImage } from '@/lib/service-preview'
</script>

<template>
  <div :style="{ '--service-art': `url(${palaceImage})` }"><RouterView /></div>
</template>
