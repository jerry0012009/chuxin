<script setup lang="ts">
import {
  Activity,
  BookOpen,
  Brain,
  Brush,
  Calendar,
  ChevronLeft,
  Eraser,
  HeartPulse,
  Home,
  LineChart,
  Palette,
  Pen,
  Save,
  Sparkles,
  Target,
  Trash2,
  Trees,
  Undo2,
  User,
  X,
} from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { multimodalAnalysis } from '@/db/api'

type Tab = 'draw' | 'evaluate' | 'history' | 'test'
type BrushType = 'pen' | 'pencil' | 'marker' | 'eraser'

interface Point {
  x: number
  y: number
}

interface Stroke {
  points: Point[]
  color: string
  width: number
  type: BrushType
}

interface Dimension {
  name: string
  score: number
  label: string
  description: string
  tone: string
}

interface HtpHistoryItem {
  id: string
  createdAt: string
  score: number
  summary: string
  dimensions: Dimension[]
  image?: string | null
}

const router = useRouter()

const activeTab = ref<Tab>('draw')
const canvasRef = ref<HTMLCanvasElement | null>(null)
const canvasWrapRef = ref<HTMLDivElement | null>(null)
const isDrawing = ref(false)
const strokes = ref<Stroke[]>([])
const currentStroke = ref<Point[]>([])
const brushType = ref<BrushType>('pen')
const brushColor = ref('#4f46e5')
const brushWidth = ref(4)
const showPalette = ref(false)
const isAnalyzing = ref(false)
const isSaving = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error'>('success')
const canvasImage = ref<string | null>(null)
const analysisResult = ref<Dimension[] | null>(null)
const analysisSummary = ref('')
const history = ref<HtpHistoryItem[]>([])
let toastTimer: number | null = null

const palette = [
  '#1e293b',
  '#64748b',
  '#94a3b8',
  '#cbd5e1',
  '#ef4444',
  '#f87171',
  '#fb923c',
  '#fbbf24',
  '#10b981',
  '#34d399',
  '#06b6d4',
  '#38bdf8',
  '#6366f1',
  '#818cf8',
  '#8b5cf6',
  '#a78bfa',
  '#d946ef',
  '#f0abfc',
  '#ec4899',
  '#f472b6',
  '#78350f',
  '#a16207',
  '#3f6212',
  '#166534',
]

const toolItems = [
  { id: 'pen' as const, label: '钢笔', icon: Pen, width: 4 },
  { id: 'pencil' as const, label: '铅笔', icon: Pen, width: 2 },
  { id: 'marker' as const, label: '马克', icon: Brush, width: 10 },
  { id: 'eraser' as const, label: '橡皮', icon: Eraser, width: 24 },
]

const methodCards = [
  {
    title: 'House. 房屋',
    subtitle: '家庭模式与安全感',
    description: '映射个体对家庭、安全感来源和核心人际关系的感受。房屋的坚固程度通常象征心理防御边界。',
    icon: Home,
    tone: 'bg-orange-50 text-orange-500',
  },
  {
    title: 'Tree. 树木',
    subtitle: '生命力与潜能',
    description: '反映自我形象、心理发展过程和环境适应能力。树木枝叶与根系细节常指向成长能量。',
    icon: Trees,
    tone: 'bg-emerald-50 text-emerald-500',
  },
  {
    title: 'Person. 人物',
    subtitle: '自我概念与边界',
    description: '呈现自我认知、人际互动模式与性格特征。人物面部和动作细节提供自尊与社交意愿线索。',
    icon: User,
    tone: 'bg-indigo-50 text-indigo-500',
  },
]

const totalScore = computed(() => {
  if (!analysisResult.value?.length) return 0
  return Math.round(analysisResult.value.reduce((sum, item) => sum + item.score, 0) / analysisResult.value.length)
})

const hasEnoughDrawing = computed(() => strokes.value.length >= 3)

const showToast = (message: string, tone: 'success' | 'error' = 'success', duration = 1800) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const clearToast = () => {
  toastMessage.value = ''
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
    toastTimer = null
  }
}

const setTool = (tool: BrushType, width: number) => {
  brushType.value = tool
  brushWidth.value = width
}

const getCanvasContext = () => canvasRef.value?.getContext('2d') || null

const drawBackground = () => {
  const canvas = canvasRef.value
  const ctx = getCanvasContext()
  if (!canvas || !ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
}

const drawStroke = (stroke: Stroke) => {
  const ctx = getCanvasContext()
  if (!ctx || stroke.points.length < 2) return
  ctx.save()
  ctx.beginPath()
  if (stroke.type === 'eraser') ctx.globalCompositeOperation = 'destination-out'
  if (stroke.type === 'marker') ctx.globalAlpha = 0.4
  if (stroke.type === 'pencil') ctx.globalAlpha = 0.65
  ctx.strokeStyle = stroke.color
  ctx.lineWidth = stroke.width
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  const firstPoint = stroke.points[0]
  if (!firstPoint) return
  ctx.moveTo(firstPoint.x, firstPoint.y)
  stroke.points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y))
  ctx.stroke()
  ctx.restore()
}

const redraw = () => {
  drawBackground()
  strokes.value.forEach(drawStroke)
}

const resizeCanvas = () => {
  const canvas = canvasRef.value
  const wrap = canvasWrapRef.value
  if (!canvas || !wrap) return
  const rect = wrap.getBoundingClientRect()
  canvas.width = Math.max(320, Math.floor(rect.width))
  canvas.height = Math.max(420, Math.floor(rect.height))
  redraw()
}

const getPoint = (event: MouseEvent | TouchEvent): Point | null => {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return null
  const source = 'touches' in event ? event.touches[0] || event.changedTouches[0] : event
  if (!source) return null
  return {
    x: source.clientX - rect.left,
    y: source.clientY - rect.top,
  }
}

const startDraw = (event: MouseEvent | TouchEvent) => {
  const point = getPoint(event)
  if (!point) return
  isDrawing.value = true
  currentStroke.value = [point]
}

const moveDraw = (event: MouseEvent | TouchEvent) => {
  if (!isDrawing.value) return
  if (event.cancelable) event.preventDefault()
  const point = getPoint(event)
  if (!point) return
  const previous = currentStroke.value[currentStroke.value.length - 1]
  currentStroke.value = [...currentStroke.value, point]
  if (!previous) return
  drawStroke({
    points: [previous, point],
    color: brushColor.value,
    width: brushWidth.value,
    type: brushType.value,
  })
}

const endDraw = () => {
  if (!isDrawing.value) return
  isDrawing.value = false
  if (currentStroke.value.length > 1) {
    strokes.value = [
      ...strokes.value,
      {
        points: currentStroke.value,
        color: brushColor.value,
        width: brushWidth.value,
        type: brushType.value,
      },
    ]
  }
  currentStroke.value = []
}

const undo = () => {
  strokes.value = strokes.value.slice(0, -1)
  redraw()
}

const clearCanvas = () => {
  strokes.value = []
  analysisResult.value = null
  analysisSummary.value = ''
  canvasImage.value = null
  clearToast()
  redraw()
}

const captureImage = () => {
  const canvas = canvasRef.value
  if (!canvas) return null
  return canvas.toDataURL('image/png')
}

const dimensionTones = ['bg-rose-50 text-rose-500', 'bg-indigo-50 text-indigo-500', 'bg-emerald-50 text-emerald-500', 'bg-amber-50 text-amber-500']

const parseHtpAiResult = (content: string) => {
  const jsonText = content.match(/\{[\s\S]*\}/)?.[0]
  if (!jsonText) throw new Error('视觉模型未返回 HTP JSON')
  const parsed = JSON.parse(jsonText)
  const summary = String(parsed.summary || parsed.analysis_summary || parsed.analysis || '').trim()
  const dimensions = Array.isArray(parsed.dimensions) ? parsed.dimensions : []
  if (!summary || dimensions.length < 4) {
    throw new Error('视觉模型返回的 HTP 报告不完整')
  }
  return {
    summary,
    dimensions: dimensions.slice(0, 4).map((item: any, index: number) => {
      const score = Number(item.score)
      if (!Number.isFinite(score)) throw new Error('视觉模型返回的 HTP 维度分数无效')
      return {
        name: String(item.name || ['内在动力', '自我防御', '生长潜能', '思维秩序'][index] || '心理维度'),
        score: Math.max(0, Math.min(100, Math.round(score))),
        label: String(item.label || item.level || '参考'),
        description: String(item.description || item.analysis || '').trim(),
        tone: dimensionTones[index] || 'bg-slate-50 text-slate-500',
      }
    }),
  }
}

const analyzeHtpImage = async (image: string) => {
  const prompt = `你是房树人 HTP 投射测评辅助分析助手。请基于用户绘制的房屋、树木、人物图像进行自我探索式分析，只返回 JSON，不要 Markdown。
JSON schema:
{
  "summary": "80-140字中文综合分析，必须提醒结果仅供自我探索参考",
  "dimensions": [
    {"name":"内在动力","score":0-100,"label":"旺盛/稳定/审慎等短标签","description":"20-40字依据"},
    {"name":"自我防御","score":0-100,"label":"严密/稳固/开放等短标签","description":"20-40字依据"},
    {"name":"生长潜能","score":0-100,"label":"极佳/活跃/蓄积等短标签","description":"20-40字依据"},
    {"name":"思维秩序","score":0-100,"label":"精准/严谨/灵活等短标签","description":"20-40字依据"}
  ]
}
必须依据图像中的构图、线条、空间、细节完整度描述，不得返回固定模板或随机分数。`
  const response = await multimodalAnalysis([
    {
      role: 'user',
      content: [
        { type: 'text', text: prompt },
        { type: 'image_url', image_url: { url: image } },
      ],
    },
  ])
  const content = String(response?.choices?.[0]?.message?.content || response?.choices?.[0]?.delta?.content || response?.text || '')
  return parseHtpAiResult(content)
}

const analyze = async () => {
  clearToast()
  if (!hasEnoughDrawing.value) {
    showToast('请至少完成 3 段绘画笔触后再开始分析', 'error')
    return
  }
  canvasImage.value = captureImage()
  if (!canvasImage.value) {
    showToast('无法读取绘画图像，请重新绘制后再试', 'error')
    return
  }
  isAnalyzing.value = true
  try {
    const report = await analyzeHtpImage(canvasImage.value)
    analysisResult.value = report.dimensions
    analysisSummary.value = report.summary
    activeTab.value = 'evaluate'
  } catch (error) {
    showToast(error instanceof Error ? `HTP分析失败：${error.message}` : 'HTP分析失败，请稍后重试', 'error')
  } finally {
    isAnalyzing.value = false
  }
}

const saveResult = async () => {
  clearToast()
  if (!analysisResult.value) return
  isSaving.value = true
  await new Promise((resolve) => window.setTimeout(resolve, 120))
  history.value = [
    {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      score: totalScore.value,
      summary: analysisSummary.value,
      dimensions: analysisResult.value,
      image: canvasImage.value,
    },
    ...history.value,
  ]
  showToast('测评结果已保存至历史记录', 'success')
  activeTab.value = 'history'
  isSaving.value = false
}

watch(activeTab, async (tab) => {
  if (tab === 'draw') {
    await nextTick()
    resizeCanvas()
  }
})

onMounted(async () => {
  await nextTick()
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCanvas)
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 dark:bg-slate-950">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
      data-testid="htp-toast"
    >
      {{ toastMessage }}
    </div>
    <header class="sticky top-0 z-40 border-b border-slate-100 bg-white/85 px-4 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/85">
      <div class="mx-auto flex max-w-3xl items-center justify-between">
        <button class="flex h-10 w-10 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800" type="button" @click="router.back()">
          <ChevronLeft class="h-6 w-6" />
        </button>
        <div class="flex items-center gap-2">
          <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <Brain class="h-5 w-5" />
          </div>
          <h1 class="text-lg font-black text-slate-900 dark:text-white">房树人心理测评</h1>
        </div>
        <div class="h-10 w-10" />
      </div>
    </header>

    <main class="mx-auto w-full max-w-3xl space-y-4 p-4">
      <nav class="mx-auto flex max-w-sm items-center rounded-2xl border border-slate-200/70 bg-slate-100/80 p-1 dark:border-slate-800 dark:bg-slate-900">
        <button
          v-for="tab in [
            { id: 'draw', label: '测验', icon: Palette },
            { id: 'evaluate', label: '结果', icon: Activity },
            { id: 'test', label: '原理', icon: BookOpen },
          ]"
          :key="tab.id"
          class="flex flex-1 items-center justify-center gap-1.5 rounded-xl py-2 text-xs font-black transition"
          :class="activeTab === tab.id || (tab.id === 'evaluate' && activeTab === 'history') ? 'bg-white text-indigo-600 shadow-sm dark:bg-slate-800' : 'text-slate-500'"
          type="button"
          :data-testid="`htp-tab-${tab.id}`"
          @click="activeTab = tab.id as Tab"
        >
          <component :is="tab.icon" class="h-3.5 w-3.5" />
          {{ tab.label }}
        </button>
      </nav>

      <section v-if="activeTab === 'draw'" class="space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-100 bg-white p-2 shadow-lg dark:border-slate-800 dark:bg-slate-900">
          <div class="flex items-center gap-1 rounded-[14px] bg-slate-50 p-1 dark:bg-slate-950">
            <button class="rounded-xl p-2 text-slate-500 hover:bg-white dark:hover:bg-slate-800" type="button" data-testid="htp-undo" @click="undo">
              <Undo2 class="h-4 w-4" />
            </button>
            <button class="rounded-xl p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40" type="button" data-testid="htp-clear" @click="clearCanvas">
              <Trash2 class="h-4 w-4" />
            </button>
          </div>

          <div class="flex flex-1 items-center justify-center gap-1">
            <button
              v-for="tool in toolItems"
              :key="tool.id"
              class="flex h-12 w-12 flex-col items-center justify-center rounded-[14px] text-[9px] font-bold transition"
              :class="brushType === tool.id ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'"
              type="button"
              :data-testid="`htp-tool-${tool.id}`"
              @click="setTool(tool.id, tool.width)"
            >
              <component :is="tool.icon" class="mb-0.5 h-4 w-4" />
              {{ tool.label }}
            </button>
          </div>

          <button
            class="h-10 w-10 rounded-[14px] border-2 border-slate-100 shadow-sm"
            type="button"
            data-testid="htp-palette-trigger"
            :style="{ backgroundColor: brushColor }"
            @click="showPalette = !showPalette"
          />
        </div>

        <div
          v-if="showPalette"
          class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/10 p-6 backdrop-blur-md"
          data-testid="htp-palette-modal"
          @click="showPalette = false"
        >
          <div
            class="w-full max-w-[320px] rounded-[36px] bg-white p-6 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.2)] dark:bg-slate-900"
            @click.stop
          >
            <div class="mb-5 flex items-center justify-between">
              <h5 class="text-[11px] font-black uppercase tracking-widest text-slate-400">Brush & Palette</h5>
              <button class="rounded-full p-1.5 text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800" type="button" aria-label="关闭调色板" @click="showPalette = false">
                <X class="h-4 w-4" />
              </button>
            </div>
            <div class="max-h-[220px] overflow-y-auto pr-1">
              <div class="mb-6 grid grid-cols-6 gap-2">
                <button
                  v-for="color in palette"
                  :key="color"
                  class="aspect-square rounded-xl border-2 transition"
                  :class="brushColor === color ? 'scale-110 border-indigo-600 shadow-sm' : 'border-slate-100'"
                  type="button"
                  :style="{ backgroundColor: color }"
                  @click="brushColor = color; showPalette = false"
                />
              </div>
            </div>
            <div class="flex items-center gap-3 border-t border-slate-50 pt-5 dark:border-slate-800">
              <div class="h-8 w-8 shrink-0 rounded-lg border border-slate-100 shadow-inner dark:border-slate-700" :style="{ backgroundColor: brushColor }" />
              <div class="flex-1 space-y-2">
                <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Width: {{ brushWidth }}PX</div>
                <input v-model.number="brushWidth" class="h-1.5 w-full accent-indigo-600" min="1" max="80" type="range" />
              </div>
            </div>
          </div>
        </div>

        <div ref="canvasWrapRef" class="relative h-[55vh] min-h-[420px] overflow-hidden rounded-[32px] border border-slate-100 bg-white shadow-2xl shadow-indigo-900/5 dark:border-slate-800">
          <canvas
            ref="canvasRef"
            class="relative z-10 block h-full w-full touch-none"
            data-testid="htp-canvas"
            @mousedown="startDraw"
            @mousemove="moveDraw"
            @mouseup="endDraw"
            @mouseleave="endDraw"
            @touchstart="startDraw"
            @touchmove="moveDraw"
            @touchend="endDraw"
          />
          <div v-if="strokes.length === 0 && !isDrawing" class="pointer-events-none absolute inset-0 flex items-center justify-center select-none text-8xl font-black italic tracking-tighter text-indigo-900 opacity-[0.03]">
            HTP
          </div>
        </div>

        <button
          class="flex h-14 w-full items-center justify-center gap-2 rounded-[20px] bg-indigo-600 text-sm font-black tracking-widest text-white shadow-lg shadow-indigo-600/20 transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          data-testid="htp-analyze"
          :disabled="isAnalyzing || !hasEnoughDrawing"
          @click="analyze"
        >
          <Sparkles class="h-4 w-4" />
          {{ isAnalyzing ? 'Processing...' : '开启 AI 心理评估' }}
        </button>
      </section>

      <section v-else-if="activeTab === 'evaluate'" class="space-y-4">
        <div v-if="!analysisResult" class="flex h-[350px] flex-col items-center justify-center rounded-[32px] border border-dashed border-slate-200 bg-white/60 dark:border-slate-800 dark:bg-slate-900/50">
          <BookOpen class="mb-3 h-10 w-10 text-slate-300" />
          <button class="rounded-xl bg-indigo-600 px-8 py-3 text-xs font-bold text-white" type="button" @click="activeTab = 'draw'">开始测验</button>
        </div>

        <template v-else>
          <div class="overflow-hidden rounded-[32px] border border-slate-100 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900" data-testid="htp-report">
            <div class="bg-slate-900 p-5 text-white">
              <div class="flex items-start justify-between">
                <div>
                  <div class="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-[0.15em] text-indigo-300">
                    <Activity class="h-3.5 w-3.5" />
                    AI Assessment Report
                  </div>
                  <h2 class="mt-1 text-base font-black">HTP 综合分析报告</h2>
                </div>
                <div class="text-right">
                  <div class="text-3xl font-black italic">{{ totalScore }}</div>
                  <div class="text-[8px] font-bold uppercase tracking-widest text-slate-400">Score</div>
                </div>
              </div>
            </div>

            <div class="space-y-4 p-4">
              <div v-if="canvasImage" class="rounded-[20px] border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-950">
                <div class="mb-2 flex items-center justify-between px-2">
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Original Drawing</span>
                  <span class="rounded-md border border-slate-200 px-2 py-0.5 text-[8px] text-slate-500">Source</span>
                </div>
                <div class="flex aspect-[4/3] items-center justify-center overflow-hidden rounded-[14px] border border-slate-100 bg-white dark:border-slate-800">
                  <img alt="User drawn HTP" class="h-full w-full object-contain" :src="canvasImage" />
                </div>
              </div>

              <div class="rounded-[20px] border border-slate-100 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950">
                <div class="mb-2 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-indigo-600">
                  <Sparkles class="h-3.5 w-3.5" />
                  Clinical Insight
                </div>
                <p class="text-sm font-medium leading-7 text-slate-700 dark:text-slate-200">{{ analysisSummary }}</p>
              </div>

              <div class="grid grid-cols-2 gap-2.5">
                <div v-for="dimension in analysisResult" :key="dimension.name" class="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                  <div :class="['flex h-9 w-9 shrink-0 items-center justify-center rounded-xl', dimension.tone]">
                    <HeartPulse v-if="dimension.name === '内在动力'" class="h-4 w-4" />
                    <Home v-else-if="dimension.name === '自我防御'" class="h-4 w-4" />
                    <Trees v-else-if="dimension.name === '生长潜能'" class="h-4 w-4" />
                    <LineChart v-else class="h-4 w-4" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="mb-0.5 flex items-center justify-between gap-1">
                      <h3 class="truncate text-xs font-black text-slate-800 dark:text-slate-100">{{ dimension.name }}</h3>
                      <span class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-black text-slate-900 dark:bg-slate-800 dark:text-slate-100">{{ dimension.score }}%</span>
                    </div>
                    <p class="truncate text-[10px] font-medium text-slate-400">{{ dimension.label }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-3 pt-2">
            <button class="flex h-14 w-full items-center justify-center gap-2 rounded-[20px] bg-indigo-600 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-indigo-600/20" type="button" data-testid="htp-save" :disabled="isSaving" @click="saveResult">
              <Save class="h-4 w-4" />
              {{ isSaving ? '保存中...' : '保存结果至历史记录' }}
            </button>
            <button class="flex h-14 w-full items-center justify-center gap-2 rounded-[20px] bg-slate-100 text-xs font-black uppercase tracking-widest text-slate-700 dark:bg-slate-800 dark:text-slate-200" type="button" data-testid="htp-open-history" @click="activeTab = 'history'">
              <Calendar class="h-4 w-4" />
              查看测验历史记录
            </button>
          </div>
        </template>
      </section>

      <section v-else-if="activeTab === 'history'" class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-black italic text-slate-800 dark:text-white">测验历程</h2>
          <span class="rounded-full border border-slate-200 px-3 py-1 text-[10px] font-bold uppercase text-slate-400 dark:border-slate-800">Total: {{ history.length }}</span>
        </div>
        <div v-if="history.length === 0" class="flex h-[360px] flex-col items-center justify-center rounded-[32px] border border-dashed border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
          <Calendar class="mb-4 h-12 w-12 text-slate-200" />
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">暂无保存记录</p>
          <button class="mt-4 text-sm font-black text-indigo-600" type="button" @click="activeTab = 'draw'">立即去画画</button>
        </div>
        <div v-else class="space-y-4" data-testid="htp-history-list">
          <article v-for="item in history" :key="item.id" class="overflow-hidden rounded-[32px] border border-slate-100 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div v-if="item.image" class="flex h-32 items-center justify-center overflow-hidden border-b border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
              <img alt="Historical drawing" class="h-full w-full object-cover opacity-80" :src="item.image" />
            </div>
            <div class="p-5">
              <div class="mb-4 flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-xs font-black text-indigo-600">{{ item.score }}</div>
                <div>
                  <div class="text-[10px] font-black uppercase tracking-widest text-slate-400">Assessment Score</div>
                  <div class="text-xs font-bold text-slate-600 dark:text-slate-300">{{ new Date(item.createdAt).toLocaleString('zh-CN') }}</div>
                </div>
              </div>
              <div class="mb-3 grid grid-cols-4 gap-2">
                <div v-for="dimension in item.dimensions" :key="dimension.name" class="flex flex-col items-center rounded-xl border border-slate-100 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-950">
                  <div class="mb-1 text-[8px] font-black uppercase leading-none text-slate-400">{{ dimension.name }}</div>
                  <div class="text-[10px] font-black leading-none text-slate-800 dark:text-slate-100">{{ dimension.score }}</div>
                  <div class="mt-1 text-[7px] font-bold text-slate-400">{{ dimension.label }}</div>
                </div>
              </div>
              <p class="text-sm leading-7 text-slate-600 dark:text-slate-300">{{ item.summary }}</p>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="space-y-6">
        <div class="space-y-2 px-2">
          <span class="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[9px] font-bold uppercase tracking-widest text-indigo-500">Clinical Methodology</span>
          <h2 class="pt-2 text-3xl font-black tracking-tight text-slate-900 dark:text-white">HTP投射<br />分析原理</h2>
          <p class="max-w-sm text-sm font-medium leading-7 text-slate-500">
            通过房屋、树木和人物绘画，在非防御状态下观察内心潜意识结构，结果仅用于自我探索。
          </p>
        </div>

        <div class="overflow-hidden rounded-[32px] border border-slate-100 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div v-for="(item, index) in methodCards" :key="item.title" class="flex items-start gap-4 p-6" :class="index !== methodCards.length - 1 ? 'border-b border-slate-100 dark:border-slate-800' : ''">
            <div :class="['flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl', item.tone]">
              <component :is="item.icon" class="h-5 w-5" />
            </div>
            <div class="space-y-1.5">
              <h3 class="text-sm font-black text-slate-800 dark:text-slate-100">{{ item.title }}</h3>
              <h4 class="text-[10px] font-bold uppercase tracking-widest text-slate-400">{{ item.subtitle }}</h4>
              <p class="pt-1 text-xs font-medium leading-6 text-slate-600 dark:text-slate-300">{{ item.description }}</p>
            </div>
          </div>
        </div>

        <div class="flex items-start gap-3 rounded-[24px] border border-slate-100 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
          <Target class="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
          <div>
            <h5 class="text-[10px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">Algorithm Note</h5>
            <p class="mt-1 text-xs font-medium leading-6 text-slate-500">
              AI 分析引擎提取绘画笔触、颜色、结构和空间分布进行综合研判，不作为医疗诊断依据。
            </p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
