<script setup lang="ts">
import { ArrowRight, Droplets, Eye, Heart, Leaf, Send, Sparkles, X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

export type MoodFeedbackType = 'giver' | 'receiver' | 'observer' | null

const props = defineProps<{
  type: MoodFeedbackType
  content: string
}>()

const emit = defineEmits<{
  close: []
  shareToTreeHole: [content: string]
}>()

const warmMessages = [
  '嘿陌生人，虽然不知道你经历了什么，但我今天吃到了超好吃的蛋糕，分你一半好运！',
  '不要难过，抬头看看天空，云朵正在为你跳舞。',
  '记得深呼吸，你已经做得很棒了，接下来的路我们一起走。',
  '世界偶尔灰暗，但你本身就是光。',
  '工作压力大吗？没关系，先抱抱自己，明天又是新的一天。',
]

const step = ref<'anim' | 'interact'>('anim')
const flipped = ref(false)
const randomMessage = ref(warmMessages[Math.floor(Math.random() * warmMessages.length)] || warmMessages[0])
let timer: number | null = null

const backdropOpacity = computed(() => (props.type === 'receiver' ? 'bg-slate-950/80' : 'bg-slate-950/60'))

watch(
  () => props.type,
  (type) => {
    if (timer) window.clearTimeout(timer)
    step.value = 'anim'
    flipped.value = false
    if (type) {
      randomMessage.value = warmMessages[Math.floor(Math.random() * warmMessages.length)] || warmMessages[0]
      timer = window.setTimeout(() => {
        step.value = 'interact'
      }, 2500)
    }
  },
  { immediate: true },
)

const close = () => emit('close')

const shareToTreeHole = () => {
  emit('shareToTreeHole', props.content)
  close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="type" class="fixed inset-0 z-[100] flex items-center justify-center pointer-events-auto">
      <div :class="['absolute inset-0 transition-opacity', backdropOpacity]" />

      <div v-if="type === 'giver'" class="relative flex h-full w-full items-center justify-center">
        <div
          v-if="step === 'anim'"
          class="h-24 w-24 animate-[feedback_giver_2s_ease-in_forwards] rounded-full bg-gradient-to-br from-amber-300 to-yellow-500 blur-xl shadow-[0_0_50px_rgba(251,191,36,0.8)]"
        />
        <section v-else class="relative z-10 w-full max-w-xs space-y-6 rounded-[32px] bg-white p-8 text-center shadow-2xl dark:bg-slate-900">
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-50">
            <Sparkles class="h-8 w-8 animate-pulse text-amber-500" />
          </div>
          <div class="space-y-2">
            <h3 class="text-xl font-black text-slate-800 dark:text-white">今天的你闪闪发光！</h3>
            <p class="text-sm leading-relaxed text-slate-500">
              你的好心情不仅治愈了自己，也可以照亮别人。愿意把这句话做成“盲盒”，留给未来某个需要安慰的人吗？
            </p>
          </div>
          <div class="space-y-3">
            <button class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-amber-500 text-sm font-bold text-white shadow-lg shadow-amber-500/20 hover:bg-amber-600" type="button" @click="shareToTreeHole">
              <Send class="mr-2 h-4 w-4" />
              存入树洞
            </button>
            <button class="inline-flex h-10 w-full items-center justify-center text-xs font-bold text-slate-400 hover:text-slate-600" type="button" @click="close">
              <Eye class="mr-2 h-4 w-4" />
              仅自己可见
            </button>
          </div>
        </section>
      </div>

      <div v-else-if="type === 'receiver'" class="relative flex h-full w-full items-center justify-center">
        <div v-if="step === 'anim'" class="flex animate-[feedback_receiver_2_5s_ease-out_forwards] flex-col items-center gap-4">
          <Leaf class="h-16 w-16 text-emerald-400/60 blur-[1px]" />
          <span class="animate-pulse font-bold tracking-widest text-white/80">接住你了...</span>
        </div>
        <section v-else class="relative z-10 h-64 w-full max-w-xs [perspective:1000px]">
          <div :class="['relative h-full w-full transition-transform duration-500 [transform-style:preserve-3d]', flipped ? '[transform:rotateY(180deg)]' : '']">
            <div class="absolute inset-0 flex flex-col items-center justify-center space-y-4 rounded-[32px] border-2 border-emerald-100/20 bg-white p-8 text-center shadow-2xl [backface-visibility:hidden] dark:bg-slate-900">
              <div class="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
                <Heart class="h-8 w-8 fill-current text-emerald-500" />
              </div>
              <h3 class="text-xl font-black text-slate-800 dark:text-white">抱抱。</h3>
              <p class="text-sm text-slate-500">树洞里有一份专门留给你的温暖...</p>
              <button class="mt-2 rounded-full bg-emerald-500 px-6 py-2 text-sm font-bold text-white hover:bg-emerald-600" type="button" @click="flipped = true">
                点击拆开
              </button>
            </div>
            <div class="absolute inset-0 flex [transform:rotateY(180deg)] flex-col items-center justify-center space-y-6 rounded-[32px] bg-gradient-to-br from-emerald-500 to-teal-600 p-8 text-center text-white shadow-2xl [backface-visibility:hidden]">
              <p class="text-sm font-medium italic leading-relaxed">“{{ randomMessage }}”</p>
              <button class="h-12 w-full rounded-2xl bg-white text-sm font-black text-emerald-600 hover:bg-white/90" type="button" @click="close">
                <Heart class="mr-2 inline h-4 w-4 fill-current" />
                收到温暖
              </button>
            </div>
          </div>
        </section>
      </div>

      <div v-else class="relative flex h-full w-full items-center justify-center">
        <div v-if="step === 'anim'" class="flex h-40 w-40 animate-[feedback_observer_2s_ease-out_forwards] items-center justify-center rounded-full border-2 border-white/30">
          <div class="h-20 w-20 rounded-full border border-white/20" />
        </div>
        <section v-else class="relative z-10 w-full max-w-xs space-y-6 rounded-[32px] bg-white p-8 text-center shadow-2xl dark:bg-slate-900">
          <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
            <Droplets class="h-8 w-8 text-blue-400" />
          </div>
          <div class="space-y-2">
            <h3 class="text-xl font-black text-slate-800 dark:text-white">平静也是一种力量。</h3>
            <p class="text-sm text-slate-500">去“树洞广场”看看吧，听听那些不曾被打扰的心跳声。</p>
          </div>
          <button class="h-12 w-full rounded-2xl bg-slate-800 text-sm font-bold text-white hover:bg-slate-900" type="button" @click="close">
            看看广场
            <ArrowRight class="ml-2 inline h-4 w-4" />
          </button>
        </section>
      </div>

      <button v-if="step === 'interact'" class="absolute right-6 top-10 grid h-10 w-10 place-items-center rounded-full text-white/40 hover:bg-white/10 hover:text-white" type="button" data-testid="mood-feedback-close" @click="close">
        <X class="h-6 w-6" />
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes feedback_giver {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  55% {
    transform: translate(20px, -100px) scale(1.2);
    opacity: 1;
  }
  100% {
    transform: translate(100px, -400px) scale(0.2);
    opacity: 0;
  }
}

@keyframes feedback_receiver {
  0% {
    transform: translate(0, -400px) rotate(-45deg);
    opacity: 0;
  }
  70% {
    transform: translate(-20px, 0) rotate(10deg);
    opacity: 1;
  }
  100% {
    transform: translate(0, 0) rotate(0);
    opacity: 1;
  }
}

@keyframes feedback_observer {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  55% {
    transform: scale(1.5);
    opacity: 0.5;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}
</style>
