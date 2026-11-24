<script setup lang="ts">
import { Menu, X } from 'lucide-vue-next'
import { computed, ref, watch, type Component } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import ServiceHero from './ServiceHero.vue'
import ServiceMasthead from './ServiceMasthead.vue'
import ServiceAccountBar from './ServiceAccountBar.vue'

const props = defineProps<{
  navigation: { path: string; label: string; icon: Component; secondary?: boolean }[]
  area: string
  title?: string
  hero?: 'compact' | 'quiet'
  home: string
}>()

const route = useRoute()
const open = ref(false)
const primary = computed(() => props.navigation.filter(item => !item.secondary))
const secondary = computed(() => props.navigation.filter(item => item.secondary))
const active = computed(() => props.navigation.filter(({ path }) => route.path === path || (path !== '/' && route.path.startsWith(`${path}/`))).sort((a, b) => b.path.length - a.path.length)[0])
watch(() => route.fullPath, () => { open.value = false })
</script>

<template>
  <div class="service-page" data-testid="service-shell">
    <ServiceMasthead :home="home" :caption="area" />
    <ServiceAccountBar />
    <nav class="service-nav" :aria-label="area" @keydown.esc="open = false">
      <div class="service-width service-nav-rail">
        <div class="service-nav-primary">
          <RouterLink v-for="item in primary" :key="item.path" :to="item.path" :aria-current="active?.path === item.path ? 'page' : undefined" @click="open = false">
            <component :is="item.icon" aria-hidden="true" />{{ item.label }}
          </RouterLink>
          <button v-if="secondary.length" class="service-more-toggle" type="button" :aria-expanded="open" aria-controls="service-navigation" :class="{ 'service-more-active': active?.secondary }" @click="open = !open">
            <X v-if="open" aria-hidden="true" /><Menu v-else aria-hidden="true" />更多服务
          </button>
        </div>
        <div v-if="secondary.length" v-show="open" id="service-navigation" class="service-nav-secondary">
          <RouterLink v-for="item in secondary" :key="item.path" :to="item.path" :aria-current="active?.path === item.path ? 'page' : undefined" @click="open = false">
            <component :is="item.icon" aria-hidden="true" />{{ item.label }}
          </RouterLink>
        </div>
      </div>
    </nav>
    <ServiceHero v-if="hero" :variant="hero" :title="title" :eyebrow="hero === 'compact' ? area : undefined" />
    <main class="service-main"><slot /></main>
  </div>
</template>
