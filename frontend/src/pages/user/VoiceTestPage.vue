<script setup lang="ts">
import { Camera, ImageIcon, Loader2, Mic, MicOff, Upload, X } from 'lucide-vue-next'
import { onBeforeUnmount, ref } from 'vue'
import { speechRecognition } from '@/db/api'
import { uploadStorageFile } from '@/lib/backend-api'
import { blobToBase64, convertWebmToWav } from '@/utils/audio'

interface SavedData {
  content: string
  imageUrls: string[]
  voiceUrl?: string
}

const content = ref('')
const imageUrls = ref<string[]>([])
const savedData = ref<SavedData | null>(null)
const isRecording = ref(false)
const isProcessing = ref(false)
const isSaving = ref(false)
const showCameraOptions = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error' | 'info'>('info')
const fileInput = ref<HTMLInputElement | null>(null)
const cameraInput = ref<HTMLInputElement | null>(null)

let mediaRecorder: MediaRecorder | null = null
let micStream: MediaStream | null = null
let asrBusy = false
let toastTimer: number | null = null

const showToast = (message: string, tone: 'success' | 'error' | 'info' = 'info', duration = 1800) => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, duration)
}

const appendRecognizedText = (text: string) => {
  const trimmed = text.trim()
  if (!trimmed) return
  content.value = content.value ? `${content.value} ${trimmed}` : trimmed
}

const transcribeChunk = async (blob: Blob) => {
  if (asrBusy || blob.size === 0) return
  asrBusy = true
  try {
    const wavBlob = await convertWebmToWav(blob)
    const base64 = await blobToBase64(wavBlob)
    const result = await speechRecognition(base64, 'wav', 16000, wavBlob.size)
    appendRecognizedText(String(result?.text || '').trim())
  } catch {
    showToast('语音识别失败，请稍后重试', 'error')
  } finally {
    asrBusy = false
  }
}

const startRecording = async () => {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000,
      },
    })
    mediaRecorder = new MediaRecorder(micStream, { mimeType: 'audio/webm;codecs=opus' })
    mediaRecorder.ondataavailable = (event) => {
      if (!isRecording.value || event.data.size === 0) return
      void transcribeChunk(event.data)
    }
    mediaRecorder.onstop = () => {
      micStream?.getTracks().forEach((track) => track.stop())
      micStream = null
    }
    mediaRecorder.start(1200)
    isRecording.value = true
    showToast('开始录音，说话时请靠近麦克风...', 'info')
  } catch (error) {
    const name = error instanceof DOMException ? error.name : ''
    if (name === 'NotAllowedError') {
      showToast('请允许访问麦克风权限', 'error')
    } else if (name === 'NotFoundError') {
      showToast('未找到麦克风设备', 'error')
    } else {
      showToast('无法访问麦克风', 'error')
    }
  }
}

const stopRecording = () => {
  if (!mediaRecorder || !isRecording.value) return
  mediaRecorder.stop()
  isRecording.value = false
  showToast('录音结束，正在识别...', 'info')
}

const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording()
    return
  }
  void startRecording()
}

const uploadImage = async (file: File) => {
  const fileExt = file.name.split('.').pop() || 'jpg'
  const fileName = `${Date.now()}_${Math.random().toString(36).substring(7)}.${fileExt}`
  const filePath = `diary-images/${fileName}`
  const data = await uploadStorageFile('diary-images', filePath, file)
  return data.publicUrl
}

const handleImageSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return

  isProcessing.value = true
  let successCount = 0
  let errorCount = 0

  try {
    const uploadedUrls: string[] = []
    for (const file of files) {
      if (file.size > 5 * 1024 * 1024) {
        errorCount += 1
        showToast(`图片 ${file.name} 超过5MB限制`, 'error')
        continue
      }
      if (!file.type.startsWith('image/')) {
        errorCount += 1
        showToast(`${file.name} 不是有效的图片文件`, 'error')
        continue
      }
      try {
        uploadedUrls.push(await uploadImage(file))
        successCount += 1
      } catch {
        errorCount += 1
      }
    }
    if (uploadedUrls.length > 0) {
      imageUrls.value = [...imageUrls.value, ...uploadedUrls]
      showToast(errorCount === 0
        ? `成功上传 ${successCount} 张图片`
        : `成功上传 ${successCount} 张图片，${errorCount} 张失败`, 'success')
    } else if (errorCount > 0) {
      showToast('所有图片上传失败', 'error')
    }
  } finally {
    isProcessing.value = false
    input.value = ''
  }
}

const removeImage = (index: number) => {
  imageUrls.value = imageUrls.value.filter((_, itemIndex) => itemIndex !== index)
  showToast('图片已删除', 'success')
}

const save = async () => {
  if (!content.value.trim() && imageUrls.value.length === 0) {
    showToast('请输入内容或上传图片', 'error')
    return
  }
  isSaving.value = true
  try {
    savedData.value = {
      content: content.value.trim(),
      imageUrls: [...imageUrls.value],
    }
    content.value = ''
    imageUrls.value = []
    showToast('测试保存成功！', 'success')
  } finally {
    isSaving.value = false
  }
}

onBeforeUnmount(() => {
  if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
  micStream?.getTracks().forEach((track) => track.stop())
  if (toastTimer) window.clearTimeout(toastTimer)
})
</script>

<template>
  <Transition name="toast-slide">
    <div
      v-if="toastMessage"
      data-testid="voice-test-toast"
      class="fixed left-1/2 top-4 z-[80] -translate-x-1/2 rounded-xl px-4 py-2 text-sm font-semibold shadow-xl"
      :class="{
        'bg-emerald-600 text-white': toastTone === 'success',
        'bg-rose-600 text-white': toastTone === 'error',
        'bg-slate-900 text-white': toastTone === 'info',
      }"
    >
      {{ toastMessage }}
    </div>
  </Transition>

  <div class="mx-auto max-w-2xl space-y-6 p-6 pb-24">
    <section class="rounded-2xl border border-slate-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
      <header class="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
        <h1 class="text-xl font-bold text-slate-900 dark:text-white">语音识别测试</h1>
      </header>
      <div class="space-y-4 p-4">
        <textarea
          v-model="content"
          class="min-h-[120px] w-full resize-none rounded-xl border-0 bg-slate-50 p-4 text-base text-slate-800 outline-none focus:ring-2 focus:ring-blue-200 dark:bg-slate-950 dark:text-slate-100"
          placeholder="写下点什么..."
        />

        <div v-if="imageUrls.length > 0" class="grid grid-cols-3 gap-2">
          <div v-for="(url, index) in imageUrls" :key="url" class="group relative">
            <img :src="url" :alt="`图片 ${index + 1}`" class="h-24 w-full rounded-lg object-cover" />
            <button class="absolute right-1 top-1 grid h-6 w-6 place-items-center rounded-full bg-rose-500 text-white opacity-0 transition group-hover:opacity-100" type="button" @click="removeImage(index)">
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between gap-3 border-t border-slate-200 pt-3 dark:border-slate-700">
          <div class="flex flex-wrap items-center gap-2">
            <button
              class="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium transition"
              :class="isRecording ? 'border border-red-200 bg-red-50 text-red-600 dark:border-red-800 dark:bg-red-950/20' : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600 dark:text-slate-300 dark:hover:bg-blue-950/20'"
              type="button"
              :disabled="isProcessing"
              @click="toggleRecording"
            >
              <Loader2 v-if="isProcessing" class="h-5 w-5 animate-spin" />
              <MicOff v-else-if="isRecording" class="h-5 w-5 animate-pulse" />
              <Mic v-else class="h-5 w-5" />
              {{ isRecording ? '停止录音' : '语音输入' }}
            </button>

            <div class="relative">
              <button class="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm text-slate-600 hover:bg-green-50 dark:text-slate-300 dark:hover:bg-green-950/20" type="button" :disabled="isProcessing" @click="showCameraOptions = !showCameraOptions">
                <ImageIcon class="h-5 w-5" />
                添加图片
              </button>
              <div v-if="showCameraOptions" class="absolute left-0 top-full z-10 mt-1 min-w-[128px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800">
                <button class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-700" type="button" @click="showCameraOptions = false; fileInput?.click()">
                  <Upload class="h-4 w-4" />
                  从相册选择
                </button>
                <button class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-700" type="button" @click="showCameraOptions = false; cameraInput?.click()">
                  <Camera class="h-4 w-4" />
                  拍照
                </button>
              </div>
            </div>

            <input ref="fileInput" class="hidden" type="file" accept="image/*" multiple @change="handleImageSelect" />
            <input ref="cameraInput" class="hidden" type="file" accept="image/*" capture="environment" @change="handleImageSelect" />

            <span v-if="isProcessing || isRecording" class="inline-flex h-7 items-center gap-1 rounded-full bg-slate-100 px-2.5 text-xs text-slate-500 dark:bg-slate-800">
              <Loader2 class="h-3 w-3 animate-spin" />
              {{ isRecording ? '录音中...' : '识别中...' }}
            </span>
          </div>

          <button
            class="h-10 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 text-sm font-bold text-white shadow-md disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            :disabled="isSaving || isProcessing || (!content.trim() && imageUrls.length === 0)"
            @click="save"
          >
            {{ isSaving ? '保存中...' : '保存记录' }}
          </button>
        </div>

        <p v-if="!content && imageUrls.length === 0 && !isRecording" class="py-2 text-center text-sm text-slate-400 dark:text-slate-500">
          支持文字输入、语音识别和图片上传
        </p>
      </div>
    </section>

    <section v-if="savedData" class="rounded-2xl border border-slate-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-900">
      <header class="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
        <h2 class="text-xl font-bold text-slate-900 dark:text-white">保存的数据</h2>
      </header>
      <div class="space-y-3 p-5 text-sm text-slate-700 dark:text-slate-200">
        <div>
          <strong>文本内容:</strong>
          <p class="mt-1 rounded bg-slate-100 p-2 dark:bg-slate-800">{{ savedData.content || '无内容' }}</p>
        </div>
        <div><strong>图片数量:</strong> {{ savedData.imageUrls.length }}</div>
        <div v-if="savedData.voiceUrl"><strong>语音文件:</strong> {{ savedData.voiceUrl }}</div>
      </div>
    </section>
  </div>
</template>
