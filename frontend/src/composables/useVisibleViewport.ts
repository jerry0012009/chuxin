import { onMounted, onUnmounted } from 'vue'

export function useVisibleViewport() {
  let viewport: VisualViewport | null = null
  const root = () => document.documentElement
  const update = () => {
    if (!viewport || viewport.scale !== 1) {
      root().style.removeProperty('--service-viewport-height')
      root().style.removeProperty('--service-viewport-top')
      return
    }
    root().style.setProperty('--service-viewport-height', `${viewport.height}px`)
    root().style.setProperty('--service-viewport-top', `${viewport.offsetTop}px`)
  }

  onMounted(() => {
    viewport = window.visualViewport
    viewport?.addEventListener('resize', update)
    viewport?.addEventListener('scroll', update)
    update()
  })
  onUnmounted(() => {
    viewport?.removeEventListener('resize', update)
    viewport?.removeEventListener('scroll', update)
    viewport = null
    update()
  })
}
