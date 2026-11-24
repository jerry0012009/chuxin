<script setup lang="ts">
import { Menu, X } from 'lucide-vue-next'
import { computed, ref, watch, type Component } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import ServiceHero from './ServiceHero.vue'
import ServiceMasthead from './ServiceMasthead.vue'
import ServiceAccountBar from './ServiceAccountBar.vue'
import '@/styles/plateau-workspace.css'

const props = defineProps<{
  navigation: { path: string; label: string; icon: Component }[]
  area: string
  title?: string
  hero?: 'compact' | 'quiet'
  home: string
}>()

const route = useRoute()
const open = ref(false)
const menuToggle = ref<HTMLButtonElement>()
function dismissNavigation() {
  if (!open.value) return
  open.value = false
  menuToggle.value?.focus()
}
const active = computed(() => props.navigation.filter(({ path }) => route.path === path || (path !== '/' && route.path.startsWith(`${path}/`))).sort((a, b) => b.path.length - a.path.length)[0])
watch(() => route.fullPath, () => { open.value = false })
</script>

<template>
  <div class="service-page plateau-workspace" data-testid="service-shell">
    <ServiceMasthead :home="home" :caption="area"><ServiceAccountBar /></ServiceMasthead>
    <nav class="service-nav" :aria-label="area" @keydown.esc="dismissNavigation">
      <div class="service-width service-nav-rail">
        <button ref="menuToggle" class="service-menu-toggle" type="button" :aria-expanded="open" aria-controls="service-navigation" @click="open = !open">
          <X v-if="open" aria-hidden="true" /><Menu v-else aria-hidden="true" />
          <span>{{ active?.label || area }}</span>
          <span class="service-menu-caption">{{ open ? '收起菜单' : '全部入口' }}</span>
        </button>
        <div id="service-navigation" class="service-nav-inner" :class="{ 'is-open': open }">
          <RouterLink v-for="item in navigation" :key="item.path" :to="item.path" :aria-current="active?.path === item.path ? 'page' : undefined" @click="open = false">
            <component :is="item.icon" aria-hidden="true" />{{ item.label }}
          </RouterLink>
        </div>
      </div>
    </nav>
    <ServiceHero v-if="hero" :variant="hero" :title="title" :eyebrow="hero === 'compact' ? area : undefined" />
    <main class="service-main"><slot /></main>
  </div>
</template>
