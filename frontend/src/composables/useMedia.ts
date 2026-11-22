import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

export const useMedia = () => {
  const width = ref(typeof window === 'undefined' ? 1440 : window.innerWidth)

  const onResize = () => {
    width.value = window.innerWidth
  }

  onMounted(() => {
    onResize()
    window.addEventListener('resize', onResize)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', onResize)
  })

  return {
    width: computed(() => width.value),
    isMobile: computed(() => width.value < 768),
    isDesktop: computed(() => width.value >= 1024),
  }
}
