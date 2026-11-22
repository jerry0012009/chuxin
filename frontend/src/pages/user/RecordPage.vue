<script setup lang="ts">
import {
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  ImagePlus,
  LoaderCircle,
  Mic,
  Pencil,
  Plus,
  Save,
  StopCircle,
  Sun,
  X,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import MoodFeedbackOverlay, { type MoodFeedbackType } from '@/components/record/MoodFeedbackOverlay.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useAppState } from '@/composables/useAppState'
import { moodMeta } from '@/data/static'
import { completeInterventionItem, completeTodayMoodInterventionIfAny, speechRecognition, updateEmotionDiary } from '@/db/api'
import type { DiaryEntry, MoodLevel } from '@/types'
import { blobToBase64, convertWebmToWav } from '@/utils/audio'

const { sortedDiaries, loadEmotionRecords, createEmotionRecord } = useAppState()
const route = useRoute()

const monthCursor = ref(new Date())
const selectedDate = ref(new Date())
const editorMood = ref<MoodLevel>('neutral')
const editorContent = ref('')
const editorTriggers = ref<string[]>([])
const editorImages = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const saving = ref(false)
const uploading = ref(false)
const inlineEditingId = ref<string | null>(null)
const inlineEditDraft = ref('')
const dayDialogOpen = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error' | 'info'>('info')
const feedbackType = ref<MoodFeedbackType>(null)
const isRecording = ref(false)
const recognitionRef = ref<any>(null)
const speechBaseContent = ref('')
const speechCommitted = ref('')
const mediaRecorder = ref<MediaRecorder | null>(null)
let voiceStream: MediaStream | null = null
let voiceAsrBusy = false
let voiceAsrErrorCount = 0
let voiceStopRequested = false
let toastTimer: number | null = null
const positiveExtra = ref<string[]>([])
const negativeExtra = ref<string[]>([])
const newPositiveTag = ref('')
const newNegativeTag = ref('')
const interventionRecordId = computed(() => String((route as any)?.query?.interventionRecordId || ''))

const positiveTriggers = ['好消息', '与朋友相聚', '顺利完成任务', '感恩时刻', '运动', '社交活动', '阳光/好天气', '音乐', '阅读', '兴趣爱好', '宠物陪伴', '冥想', '健康饮食']
const negativeTriggers = ['睡眠不足', '工作压力', '家庭琐事', '天气阴郁', '身体不适', '学习困难', '人际关系', '经济压力', '饮食不规律', '通勤拥堵', '争执/冲突', '其他']
const positivePresetSet = new Set(positiveTriggers)
const negativePresetSet = new Set(negativeTriggers)

const dateKey = (date: Date) => date.toISOString().slice(0, 10)

const monthLabel = computed(() =>
  monthCursor.value.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' }),
)

const selectedDateKey = computed(() => dateKey(selectedDate.value))
const selectedDateLabel = computed(() =>
  selectedDate.value.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }),
)

const moodEntries = Object.entries(moodMeta) as Array<[MoodLevel, (typeof moodMeta)[MoodLevel]]>

const calendarDays = computed(() => {
  const year = monthCursor.value.getFullYear()
  const month = monthCursor.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const start = firstDay.getDay()
  const days: Array<Date | null> = []
  for (let i = 0; i < start; i += 1) days.push(null)
  for (let day = 1; day <= lastDay.getDate(); day += 1) days.push(new Date(year, month, day))
  return days
})

const diariesByDate = computed(() => {
  const map = new Map<string, DiaryEntry[]>()
  sortedDiaries.value.forEach((item) => {
    const list = map.get(item.date) || []
    list.push(item)
    map.set(item.date, list)
  })
  return map
})

const currentDateEntries = computed(() => diariesByDate.value.get(selectedDateKey.value) || [])
const currentDateDiary = computed(() => currentDateEntries.value[0] || null)
const selectedDateDialogTitle = computed(() =>
  selectedDate.value.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }),
)
const selectedDateWeekday = computed(() =>
  selectedDate.value.toLocaleDateString('zh-CN', { weekday: 'long' }),
)
const isSelectedDateToday = computed(() => selectedDateKey.value === dateKey(new Date()))

const selectedPositiveTriggers = computed(() =>
  editorTriggers.value.filter((item) => positivePresetSet.has(item) || positiveExtra.value.includes(item)),
)

const selectedNegativeTriggers = computed(() =>
  editorTriggers.value.filter((item) => negativePresetSet.has(item) || negativeExtra.value.includes(item)),
)

const showToast = (message: string, tone: 'success' | 'error' | 'info' = 'info', duration = 1200) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const clearMessages = () => {
  toastMessage.value = ''
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
    toastTimer = null
  }
}

const shiftMonth = (offset: number) => {
  monthCursor.value = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth() + offset, 1)
}

const selectMood = (mood: MoodLevel) => {
  editorMood.value = mood
}

const toggleTrigger = (item: string) => {
  editorTriggers.value = editorTriggers.value.includes(item)
    ? editorTriggers.value.filter((tag) => tag !== item)
    : [...editorTriggers.value, item]
}

const removeEditorImage = (index: number) => {
  editorImages.value = editorImages.value.filter((_, currentIndex) => currentIndex !== index)
}

const addTrigger = (value: string, bucket: 'positive' | 'negative') => {
  const normalized = value.trim()
  if (!normalized) return
  const target = bucket === 'positive' ? positiveExtra : negativeExtra
  if (!target.value.includes(normalized)) {
    target.value = [...target.value, normalized]
  }
  if (!editorTriggers.value.includes(normalized)) {
    editorTriggers.value = [...editorTriggers.value, normalized]
  }
}

const addPositiveTrigger = () => {
  addTrigger(newPositiveTag.value, 'positive')
  newPositiveTag.value = ''
}

const addNegativeTrigger = () => {
  addTrigger(newNegativeTag.value, 'negative')
  newNegativeTag.value = ''
}

const syncEditorFromDiary = (diary: DiaryEntry | null) => {
  if (!diary) {
    editorMood.value = 'neutral'
    editorContent.value = ''
    editorTriggers.value = []
    editorImages.value = []
    return
  }
  editorMood.value = diary.mood
  editorContent.value = diary.content
  editorTriggers.value = [...diary.triggers]
  editorImages.value = [...diary.images]
}

const pickDate = (date: Date, options: { sync?: boolean } = { sync: true }) => {
  selectedDate.value = date
  inlineEditingId.value = null
  clearMessages()
  if (options.sync !== false) {
    const diary = diariesByDate.value.get(dateKey(date))?.[0] || null
    syncEditorFromDiary(diary)
    if (diary) {
      inlineEditingId.value = diary.id
      inlineEditDraft.value = diary.content
      dayDialogOpen.value = true
    }
  }
}

const openInlineEdit = (item: DiaryEntry) => {
  inlineEditingId.value = item.id
  inlineEditDraft.value = item.content
}

const saveInlineEdit = async (item: DiaryEntry) => {
  saving.value = true
  clearMessages()
  try {
    await updateEmotionDiary(item.id, {
      content: inlineEditDraft.value,
    })
    await loadEmotionRecords()
    inlineEditingId.value = null
    showToast('已更新', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '正文更新失败', 'error')
  } finally {
    saving.value = false
  }
}

const updateDiaryMood = async (item: DiaryEntry, mood: MoodLevel) => {
  saving.value = true
  clearMessages()
  try {
    await updateEmotionDiary(item.id, { emotion_level: mood })
    await loadEmotionRecords()
    editorMood.value = mood
    showToast('当天情绪已更新', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '更新失败', 'error')
  } finally {
    saving.value = false
  }
}

const normalizeDiaryImageUrl = (url: string) => {
  if (url.startsWith('/srcs/enjoy/')) {
    return `${import.meta.env.BASE_URL}${url.replace(/^\/+/, '')}`
  }
  return url
}

const getBundledEmotionImageUrl = (name: string) =>
  `${import.meta.env.BASE_URL}srcs/enjoy/${encodeURIComponent(name)}`

const handleDiaryImageUpload = async (item: DiaryEntry, files: FileList | null, replaceIndex?: number) => {
  if (!files?.length) return
  saving.value = true
  clearMessages()
  try {
    const nextImages: string[] = []
    for (const file of Array.from(files)) {
      if (file.size > 10 * 1024 * 1024) {
        showToast(`${file.name} 超过10MB，已跳过`, 'error')
        continue
      }
      const base64 = await blobToBase64(file)
      nextImages.push(`data:${file.type || 'image/png'};base64,${base64}`)
    }
    if (!nextImages.length) return
    const currentImages = [...item.images]
    const mergedImages =
      typeof replaceIndex === 'number'
        ? currentImages.map((image, index) => (index === replaceIndex ? nextImages[0]! : image))
        : [...currentImages, ...nextImages]
    await updateEmotionDiary(item.id, { image_urls: mergedImages })
    await loadEmotionRecords()
    showToast('图片已更新', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '图片更新失败', 'error')
  } finally {
    saving.value = false
  }
}

const promptUploadForDiary = (item: DiaryEntry, replaceIndex?: number) => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.multiple = typeof replaceIndex !== 'number'
  input.onchange = () => {
    void handleDiaryImageUpload(item, input.files, replaceIndex)
  }
  input.click()
}

const switchDiaryBundledImage = async (item: DiaryEntry, imageName: string) => {
  saving.value = true
  clearMessages()
  try {
    await updateEmotionDiary(item.id, { image_urls: [getBundledEmotionImageUrl(imageName)] })
    await loadEmotionRecords()
    showToast('图片已切换', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '切换失败', 'error')
  } finally {
    saving.value = false
  }
}

const uploadEditorImages = async (event: Event) => {
  const target = event.target as HTMLInputElement | null
  const files = target?.files
  if (!files?.length) return

  uploading.value = true
  clearMessages()
  try {
    const nextImages: string[] = []
    for (const file of Array.from(files)) {
      if (file.size > 10 * 1024 * 1024) {
        showToast(`${file.name} 超过10MB，已跳过`, 'error')
        continue
      }
      const base64 = await blobToBase64(file)
      nextImages.push(`data:${file.type || 'image/png'};base64,${base64}`)
    }
    editorImages.value = [...editorImages.value, ...nextImages]
    if (nextImages.length) showToast('图片已加入当前草稿', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '图片处理失败', 'error')
  } finally {
    uploading.value = false
    if (target) {
      target.value = ''
    }
  }
}

const appendVoiceText = (text: string) => {
  const normalized = text.trim()
  if (!normalized) return
  editorContent.value = editorContent.value
    ? [editorContent.value, normalized].filter(Boolean).join('\n')
    : normalized
}

const inferAudioFormat = (blob: Blob): 'wav' | 'm4a' | 'webm' | 'ogg' | 'mp3' => {
  const type = blob.type.toLowerCase()
  if (type.includes('webm')) return 'webm'
  if (type.includes('ogg')) return 'ogg'
  if (type.includes('mpeg') || type.includes('mp3')) return 'mp3'
  if (type.includes('mp4') || type.includes('m4a')) return 'm4a'
  return 'wav'
}

const transcribeVoiceChunk = async (blob: Blob) => {
  if (!blob || blob.size <= 0) return
  const shouldConvertToWav = /webm|ogg|opus/i.test(blob.type || '')
  const wavBlob = shouldConvertToWav ? await convertWebmToWav(blob) : blob
  const base64 = await blobToBase64(wavBlob)
  const result = await speechRecognition(base64, inferAudioFormat(wavBlob), 16000, wavBlob.size)
  const text = String(result?.text || result?.result?.[0] || '').trim()
  if (!text) {
    throw new Error('语音服务未返回转写文本')
  }
  appendVoiceText(text)
}

const stopVoiceStream = () => {
  voiceStream?.getTracks().forEach((track) => track.stop())
  voiceStream = null
}

const handleVoiceChunk = (blob: Blob) => {
  if (!blob || blob.size <= 0 || voiceAsrBusy) return
  voiceAsrBusy = true
  void transcribeVoiceChunk(blob)
    .then(() => {
      voiceAsrErrorCount = 0
    })
    .catch((error) => {
      voiceAsrErrorCount += 1
      if (voiceAsrErrorCount >= 2 && !voiceStopRequested) {
        showToast('网络语音识别不稳定，已继续使用浏览器识别', 'info')
        try {
          startWebSpeechFallback()
        } catch {
          stopVoiceInput()
        }
      }
    })
    .finally(() => {
      voiceAsrBusy = false
    })
}

const startWebSpeechFallback = () => {
  clearMessages()
  const SpeechRecognitionCtor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognitionCtor) {
    throw new Error('当前浏览器不支持语音识别')
  }

  const recognition = new SpeechRecognitionCtor()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  speechBaseContent.value = editorContent.value
  speechCommitted.value = ''

  recognition.onresult = (event: any) => {
    let committed = ''
    let interim = ''
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const result = event.results[index]
      const transcript = result?.[0]?.transcript || ''
      if (result?.isFinal) {
        committed += transcript
      } else {
        interim += transcript
      }
    }
    if (committed) {
      speechCommitted.value = `${speechCommitted.value}${committed}`.trim()
    }
    const merged = `${speechCommitted.value}${interim}`.trim()
    editorContent.value = speechBaseContent.value
      ? [speechBaseContent.value, merged].filter(Boolean).join('\n')
      : merged
  }

  recognition.onerror = () => {
    isRecording.value = false
    if (speechCommitted.value.trim() || editorContent.value.trim() !== speechBaseContent.value.trim()) {
      showToast('语音识别已写入日记', 'success')
      return
    }
    showToast('语音识别已中断，请重试', 'error')
  }

  recognition.onend = () => {
    if (isRecording.value) {
      try {
        recognition.start()
      } catch {
        isRecording.value = false
      }
    }
  }

  try {
    recognition.start()
    recognitionRef.value = recognition
    isRecording.value = true
    showToast('浏览器语音识别中...', 'info')
  } catch {
    throw new Error('无法启动语音识别')
  }
}

const startVoiceInput = async () => {
  clearMessages()
  voiceAsrBusy = false
  voiceAsrErrorCount = 0
  voiceStopRequested = false

  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      startWebSpeechFallback()
      return
    }
    voiceStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
    const recorder = new MediaRecorder(voiceStream, { mimeType: 'audio/webm;codecs=opus' })
    mediaRecorder.value = recorder
    recorder.ondataavailable = (event) => {
      if (!isRecording.value) return
      if (event.data?.size > 0) handleVoiceChunk(event.data)
    }
    recorder.onstop = () => {
      stopVoiceStream()
    }
    recorder.start(800)
    isRecording.value = true
    showToast('语音识别中...', 'info')
  } catch (error) {
    stopVoiceStream()
    try {
      startWebSpeechFallback()
    } catch {
      showToast(error instanceof Error ? `无法访问麦克风：${error.message}` : '无法访问麦克风', 'error')
    }
  }
}

const stopVoiceInput = () => {
  voiceStopRequested = true
  isRecording.value = false
  if (recognitionRef.value) {
    try {
      recognitionRef.value.stop()
    } catch {
      // ignore stop errors from browser implementation
    }
    recognitionRef.value = null
  }
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  } else {
    stopVoiceStream()
  }
  mediaRecorder.value = null
}

const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopVoiceInput()
    return
  }
  startVoiceInput()
}

const saveCurrentDiary = async () => {
  if (!editorContent.value.trim() && editorImages.value.length === 0) {
    showToast('请写下你的心情或上传图片', 'error')
    return
  }
  const existed = !!currentDateDiary.value
  saving.value = true
  clearMessages()
  try {
    const saved = await createEmotionRecord({
      date: selectedDateKey.value,
      mood: editorMood.value,
      content: editorContent.value,
      triggers: editorTriggers.value,
      images: editorImages.value,
    })
    if (saved) {
      syncEditorFromDiary(saved)
      await loadEmotionRecords()
      const summary = {
        mood: editorMood.value,
        triggerCount: editorTriggers.value.length,
        contentLength: editorContent.value.trim().length,
      }
      if (interventionRecordId.value) {
        await completeInterventionItem(interventionRecordId.value, {
          source_ref_table: 'emotion_diaries',
          source_ref_id: saved.id,
          duration_seconds: 0,
          summary_json: summary,
        }).catch((error) => showToast(error instanceof Error ? error.message : '日记已保存，但任务同步失败', 'error'))
      } else {
        void completeTodayMoodInterventionIfAny({
          source_ref_table: 'emotion_diaries',
          source_ref_id: saved.id,
          duration_seconds: 0,
          summary_json: summary,
        }).catch(() => {})
      }
      showToast(existed ? '记录已更新' : '记录已保存', 'success')
      if (editorMood.value === 'very_good' || editorMood.value === 'good') {
        feedbackType.value = 'giver'
      } else if (editorMood.value === 'bad' || editorMood.value === 'very_bad') {
        feedbackType.value = 'receiver'
      } else {
        feedbackType.value = 'observer'
      }
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存失败,请重试', 'error')
  } finally {
    saving.value = false
  }
}

const closeMoodFeedback = () => {
  feedbackType.value = null
}

const shareMoodToTreeHole = () => {
  showToast('已存入树洞，愿这份温暖继续传递', 'success', 1500)
}

const formatDiaryTime = (item: DiaryEntry) => {
  if (!item.createdAt) return item.date
  return new Date(item.createdAt).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatDiaryClock = (item: DiaryEntry) => {
  if (!item.createdAt) return ''
  return new Date(item.createdAt).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

pickDate(new Date(), { sync: false })

onMounted(() => {
  void loadEmotionRecords()
})

onBeforeUnmount(() => {
  stopVoiceInput()
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pb-24 dark:from-slate-950 dark:to-slate-950">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : toastTone === 'success' ? 'bg-emerald-600 shadow-emerald-900/20' : 'bg-slate-950 shadow-slate-900/20'"
      data-testid="record-toast"
    >
      {{ toastMessage }}
    </div>
    <div class="sticky top-0 z-20 border-b border-slate-100 bg-white/80 px-4 py-3 backdrop-blur md:px-8 dark:border-slate-800 dark:bg-slate-950/80">
      <div class="mx-auto flex max-w-7xl items-center justify-between gap-3">
        <div class="min-w-0 flex-1">
          <h1 class="truncate text-[20px] font-black text-slate-800 dark:text-white md:text-xl">情绪日记</h1>
        </div>
        <div class="flex shrink-0 items-center gap-2 rounded-full border border-blue-100 bg-blue-50/60 px-3 py-2 shadow-sm dark:border-blue-900/50 dark:bg-blue-950/40">
          <div class="flex flex-col items-end leading-tight">
            <span class="hidden text-[10px] font-bold tracking-wider text-blue-400 sm:block">TODAY'S WEATHER</span>
            <span class="text-sm font-bold text-blue-600 dark:text-blue-300">晴转多云 · 18°C</span>
          </div>
          <div class="flex h-7 w-7 items-center justify-center rounded-full bg-white shadow-sm dark:bg-slate-900">
            <Sun class="h-5 w-5 text-amber-400" />
          </div>
        </div>
      </div>
    </div>

    <div class="page-grid py-8">
      <SectionTitle
        eyebrow="Emotion Diary"
        title="情绪记录"
        description="记录今天的心情、触发因素和身体感受，帮助你更稳定地觉察情绪变化。"
      />

      <div class="mt-6 grid gap-6 lg:grid-cols-3">
      <div class="space-y-6 lg:col-span-2">
        <BaseCard>
          <div class="mb-4 flex items-center justify-between">
            <button class="rounded-full border border-slate-200 p-2 dark:border-slate-700" @click="shiftMonth(-1)">
              <ChevronLeft class="h-4 w-4" />
            </button>
            <p class="font-semibold text-slate-900 dark:text-white">{{ monthLabel }}</p>
            <button class="rounded-full border border-slate-200 p-2 dark:border-slate-700" @click="shiftMonth(1)">
              <ChevronRight class="h-4 w-4" />
            </button>
          </div>

          <div class="mb-3 grid grid-cols-7 gap-2 text-center text-xs text-slate-400">
            <span v-for="item in ['日', '一', '二', '三', '四', '五', '六']" :key="item">{{ item }}</span>
          </div>

          <div class="grid grid-cols-7 gap-2">
            <div v-for="(date, index) in calendarDays" :key="index" class="aspect-square">
              <button
                v-if="date"
                class="flex h-full w-full flex-col items-center justify-center rounded-2xl border text-sm transition"
                :class="
                  selectedDateKey === dateKey(date)
                    ? 'border-primary bg-primary/10 text-primary'
                    : diariesByDate.get(dateKey(date))?.length
                      ? 'border-slate-200 bg-slate-50 text-slate-800 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200'
                      : 'border-slate-100 bg-slate-50 hover:border-slate-200 dark:border-slate-800 dark:bg-slate-900'
                "
                :data-testid="`record-calendar-day-${dateKey(date)}`"
                @click="pickDate(date)"
              >
                <span>{{ date.getDate() }}</span>
                <span class="text-xs">
                  {{ diariesByDate.get(dateKey(date))?.[0] ? moodMeta[diariesByDate.get(dateKey(date))![0]!.mood].emoji : '' }}
                </span>
              </button>
            </div>
          </div>
        </BaseCard>

      </div>

      <div class="space-y-6 lg:col-span-1">
        <BaseCard>
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm text-slate-500">{{ selectedDateKey }}</p>
              <h3 class="text-xl font-bold text-slate-900 dark:text-white">记录此时心情</h3>
              <p class="mt-1 text-sm text-slate-500">{{ selectedDateLabel }}</p>
            </div>
            <button
              data-testid="save-emotion-record"
              class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white dark:bg-white dark:text-slate-900"
              :disabled="saving"
              @click="saveCurrentDiary"
            >
              <span class="inline-flex items-center gap-2">
                <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" />
                <Save v-else class="h-4 w-4" />
                保存记录
              </span>
            </button>
          </div>

          <h4 class="mt-5 text-sm font-medium text-slate-900 dark:text-white">今天感觉如何?</h4>
          <div class="mt-3 grid gap-3 sm:grid-cols-5">
            <button
              v-for="[key, meta] in moodEntries"
              :key="key"
              :data-testid="`mood-option-${key}`"
              class="rounded-3xl border px-3 py-4 transition"
              :class="editorMood === key ? meta.tone + ' border-current' : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900'"
              @click="selectMood(key)"
            >
              <div class="text-2xl">{{ meta.emoji }}</div>
              <p class="mt-2 text-sm font-semibold">{{ meta.label }}</p>
            </button>
          </div>

          <div class="mt-5">
            <div class="mb-3 flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold text-slate-900 dark:text-white">随手记</p>
              </div>
              <div class="flex gap-2">
                <button
                  data-testid="record-voice-trigger"
                  class="rounded-2xl px-4 py-3 text-sm font-semibold transition"
                  :class="isRecording ? 'bg-rose-500 text-white shadow-lg shadow-rose-200 dark:shadow-none' : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'"
                  :disabled="saving"
                  @click="toggleVoiceInput"
                >
                  <span class="inline-flex items-center gap-2">
                    <StopCircle v-if="isRecording" class="h-4 w-4" />
                    <Mic v-else class="h-4 w-4" />
                    {{ isRecording ? '停止' : '语音' }}
                  </span>
                </button>
                <button
                  class="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  :disabled="uploading"
                  @click="fileInput?.click()"
                >
                  <span class="inline-flex items-center gap-2">
                    <LoaderCircle v-if="uploading" class="h-4 w-4 animate-spin" />
                    <ImagePlus v-else class="h-4 w-4" />
                    图片
                  </span>
                </button>
              </div>
            </div>

            <textarea
              v-model="editorContent"
              class="min-h-40 w-full rounded-[24px] border border-slate-200 bg-slate-50 px-4 py-4 text-sm outline-none ring-0 placeholder:text-slate-400 dark:border-slate-800 dark:bg-slate-900"
              data-testid="record-content-input"
              placeholder="写下点什么..."
            />
          </div>

          <div class="mt-5 grid gap-4 lg:grid-cols-2">
            <div class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
              <div class="mb-3 flex items-center justify-between">
                <div>
                  <p class="text-sm font-semibold text-slate-900 dark:text-white">积极触发因素</p>
                  <p class="mt-1 text-xs text-slate-500">记录让你感觉更好的瞬间。</p>
                </div>
                <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-500 shadow-sm dark:bg-slate-950 dark:text-slate-300">{{ selectedPositiveTriggers.length }} 项</span>
              </div>

              <div class="flex flex-wrap gap-2">
                <button
                  v-for="item in [...positiveTriggers, ...positiveExtra]"
                  :key="item"
                  class="rounded-full px-4 py-2 text-sm transition"
                  :class="editorTriggers.includes(item) ? 'bg-sky-600 text-white' : 'bg-white text-slate-600 shadow-sm dark:bg-slate-950 dark:text-slate-300'"
                  @click="toggleTrigger(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-3 flex gap-2">
                <input
                  v-model="newPositiveTag"
                  data-testid="record-positive-trigger-input"
                  class="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-950"
                  placeholder="补充积极事件"
                  @keydown.enter.prevent="addPositiveTrigger"
                />
                <button
                  class="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm dark:bg-slate-950 dark:text-slate-200"
                  @click="addPositiveTrigger"
                >
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            </div>

            <div class="rounded-[24px] bg-slate-50 p-4 dark:bg-slate-900">
              <div class="mb-3 flex items-center justify-between">
                <div>
                  <p class="text-sm font-semibold text-slate-900 dark:text-white">压力触发因素</p>
                  <p class="mt-1 text-xs text-slate-500">记录让你紧绷或消耗的来源。</p>
                </div>
                <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-500 shadow-sm dark:bg-slate-950 dark:text-slate-300">{{ selectedNegativeTriggers.length }} 项</span>
              </div>

              <div class="flex flex-wrap gap-2">
                <button
                  v-for="item in [...negativeTriggers, ...negativeExtra]"
                  :key="item"
                  class="rounded-full px-4 py-2 text-sm transition"
                  :class="editorTriggers.includes(item) ? 'bg-rose-500 text-white' : 'bg-white text-slate-600 shadow-sm dark:bg-slate-950 dark:text-slate-300'"
                  @click="toggleTrigger(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-3 flex gap-2">
                <input
                  v-model="newNegativeTag"
                  data-testid="record-negative-trigger-input"
                  class="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-950"
                  placeholder="补充压力来源"
                  @keydown.enter.prevent="addNegativeTrigger"
                />
                <button
                  class="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm dark:bg-slate-950 dark:text-slate-200"
                  @click="addNegativeTrigger"
                >
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div class="mt-5 rounded-[24px] border border-dashed border-slate-200 p-4 dark:border-slate-800">
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="font-semibold text-slate-900 dark:text-white">图片记录</p>
                <p class="mt-1 text-sm text-slate-500">用图片补充此刻的场景、物品或让你有感受的瞬间。</p>
              </div>
              <button
                class="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                :disabled="uploading"
                @click="fileInput?.click()"
              >
                <span class="inline-flex items-center gap-2">
                  <LoaderCircle v-if="uploading" class="h-4 w-4 animate-spin" />
                  <ImagePlus v-else class="h-4 w-4" />
                  添加图片
                </span>
              </button>
              <input ref="fileInput" class="hidden" multiple accept="image/*" type="file" @change="uploadEditorImages" />
            </div>

            <div v-if="editorImages.length" class="mt-4 grid gap-3 sm:grid-cols-4">
              <div v-for="(image, index) in editorImages" :key="`${image}-${index}`" class="relative overflow-hidden rounded-[20px]">
                <img :src="image" alt="" class="h-28 w-full object-cover" />
                <button
                  class="absolute right-2 top-2 rounded-full bg-black/60 p-1 text-white"
                  @click="removeEditorImage(index)"
                >
                  <X class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

        </BaseCard>

      </div>
    </div>
    </div>

    <div
      v-if="dayDialogOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm"
      data-testid="record-day-dialog"
      @click.self="dayDialogOpen = false"
    >
      <div class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[28px] bg-white shadow-2xl dark:bg-slate-950">
        <div class="border-b border-slate-100 bg-gradient-to-r from-primary/10 to-primary/5 px-6 py-5 dark:border-slate-800">
          <div class="flex items-center justify-between gap-4">
            <div class="space-y-1">
              <h3 class="text-lg font-black text-slate-900 dark:text-white">{{ selectedDateDialogTitle }}</h3>
              <p class="text-[11px] text-slate-500">{{ selectedDateWeekday }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span v-for="item in currentDateEntries.slice(0, 3)" :key="item.id" class="text-xl">
                {{ moodMeta[item.mood].emoji }}
              </span>
              <button class="rounded-full p-2 text-slate-500 transition hover:bg-white/80 dark:hover:bg-slate-900" @click="dayDialogOpen = false">
                <X class="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        <div class="space-y-4 p-6">
          <div v-if="isSelectedDateToday && currentDateDiary" class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div class="mb-3 flex items-center justify-between gap-4">
              <h4 class="text-sm font-bold text-slate-900 dark:text-white">编辑当天情绪</h4>
              <span v-if="formatDiaryClock(currentDateDiary)" class="text-xs text-slate-500">
                最近记录：{{ formatDiaryClock(currentDateDiary) }}
              </span>
            </div>
            <div class="mb-3 grid grid-cols-5 gap-2">
              <button
                v-for="[key, meta] in moodEntries"
                :key="key"
                class="flex flex-col items-center gap-1 rounded-xl border p-3 transition"
                :class="currentDateDiary.mood === key ? meta.tone + ' border-current' : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900'"
                :disabled="saving"
                @click="updateDiaryMood(currentDateDiary, key)"
              >
                <span class="text-2xl">{{ meta.emoji }}</span>
                <span class="text-xs font-medium">{{ meta.label }}</span>
              </button>
            </div>
            <div>
              <h4 class="mb-2 text-sm font-medium text-slate-900 dark:text-white">切换图片</h4>
              <div class="grid grid-cols-4 gap-2 sm:grid-cols-6">
                <button
                  v-for="name in ['开心_1.png', '喜悦恋爱_1.png', '治愈温暖_1.png', '惊讶_1.png', '困倦_1.png', '悲伤_1.png', '生气_1.png', '害怕_1.png']"
                  :key="name"
                  class="aspect-square overflow-hidden rounded-lg border border-slate-200 bg-slate-50 transition hover:shadow dark:border-slate-800 dark:bg-slate-900"
                  :disabled="saving"
                  @click="switchDiaryBundledImage(currentDateDiary, name)"
                >
                  <img :src="getBundledEmotionImageUrl(name)" :alt="name" class="h-full w-full object-cover" />
                </button>
              </div>
            </div>
          </div>

          <div v-for="item in currentDateEntries" :key="item.id" class="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div class="flex gap-4 p-4">
              <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-2xl dark:bg-slate-800">
                {{ moodMeta[item.mood].emoji }}
              </div>
              <div class="min-w-0 flex-1 space-y-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tag in item.triggers"
                      :key="tag"
                      class="rounded-full border border-slate-200 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800"
                    >
                      {{ tag }}
                    </span>
                  </div>
                  <button
                    class="h-8 rounded-xl px-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900"
                    @click="inlineEditingId === item.id ? (inlineEditingId = null) : openInlineEdit(item)"
                  >
                    {{ inlineEditingId === item.id ? '取消' : '编辑' }}
                  </button>
                </div>

                <div v-if="inlineEditingId === item.id" class="space-y-2">
                  <textarea
                    v-model="inlineEditDraft"
                    class="min-h-32 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none dark:border-slate-800 dark:bg-slate-900"
                  />
                  <div class="flex justify-end">
                    <button
                      class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white dark:bg-white dark:text-slate-950"
                      :disabled="saving"
                      @click="saveInlineEdit(item)"
                    >
                      <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" />
                      <Check v-else class="h-4 w-4" />
                      完成
                    </button>
                  </div>
                </div>
                <p v-else class="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                  {{ item.content || '暂无内容' }}
                </p>

                <div v-if="item.images.length" class="grid grid-cols-3 gap-2">
                  <button
                    v-for="(image, index) in item.images"
                    :key="`${item.id}-${index}`"
                    class="aspect-square overflow-hidden rounded-lg border border-slate-200 transition hover:shadow dark:border-slate-800"
                    title="点击替换此图片"
                    @click="promptUploadForDiary(item, index)"
                  >
                    <img :src="normalizeDiaryImageUrl(image)" :alt="`dimg-${index}`" class="h-full w-full object-cover" />
                  </button>
                  <button
                    class="flex aspect-square items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-slate-300 text-xs text-slate-500 transition hover:border-primary hover:text-primary dark:border-slate-700"
                    title="添加图片"
                    @click="promptUploadForDiary(item)"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 pb-6">
          <button class="h-11 w-full rounded-xl border border-slate-200 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900" @click="dayDialogOpen = false">
            关闭
          </button>
        </div>
      </div>
    </div>

    <MoodFeedbackOverlay
      :type="feedbackType"
      :content="editorContent"
      @close="closeMoodFeedback"
      @share-to-tree-hole="shareMoodToTreeHole"
    />
  </div>
</template>
