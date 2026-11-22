<script setup lang="ts">
import { Calendar, ChevronLeft, Mail, MessageSquare, Phone, Ruler, Save, Scale, User } from 'lucide-vue-next'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppState } from '@/composables/useAppState'
import { useAuthSession } from '@/composables/useAuthSession'
import { updateProfile } from '@/db/api'

const router = useRouter()
const { state, refreshCurrentAccountProfile } = useAppState()
const { state: authState } = useAuthSession()
const loading = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error'>('success')
let autoSaveTimer: number | null = null
let toastTimer: number | null = null

const form = reactive({
  full_name: '',
  gender: 'other',
  age: '',
  height: '',
  weight: '',
  phone: '',
  wechat: '',
  email: '',
})

const ages = computed(() => Array.from({ length: 100 }, (_, index) => `${index + 1}`))

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

const calculateAge = (birthDate?: string | null) => {
  if (!birthDate) return ''
  const today = new Date()
  const birth = new Date(birthDate)
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age -= 1
  }
  return age > 0 ? String(age) : ''
}

const parseBio = (value?: string | null) => {
  try {
    return value ? JSON.parse(value) as Record<string, unknown> : {}
  } catch {
    return {}
  }
}

watch(
  () => authState.profile,
  (profile) => {
    const bio = parseBio(profile?.bio)
    form.full_name = profile?.full_name || ''
    form.gender = profile?.gender || 'other'
    form.age = calculateAge(profile?.birth_date)
    form.height = bio.height ? String(bio.height) : ''
    form.weight = bio.weight ? String(bio.weight) : ''
    form.phone = profile?.phone || state.profile.phoneNumber || ''
    form.wechat = profile?.wechat || ''
    form.email = profile?.email || ''
  },
  { immediate: true, deep: true },
)

const save = async () => {
  if (!authState.user) return
  clearToast()

  const height = Number(form.height)
  if (form.height && (Number.isNaN(height) || height < 50 || height > 250)) {
    showToast('请输入有效的身高 (50-250cm)', 'error')
    return
  }

  loading.value = true
  try {
    const bio = parseBio(authState.profile?.bio)
    if (form.height) bio.height = height
    else delete bio.height
    const weight = Number(form.weight)
    if (form.weight) bio.weight = weight
    else delete bio.weight

    const age = Number(form.age)
    const birthDate = form.age && !Number.isNaN(age) && age > 0
      ? `${new Date().getFullYear() - age}-01-01`
      : undefined

    await updateProfile(authState.user.id, {
      full_name: form.full_name,
      gender: form.gender,
      phone: form.phone,
      wechat: form.wechat,
      email: form.email,
      role: authState.profile?.role || 'user',
      birth_date: birthDate,
      bio: Object.keys(bio).length > 0 ? JSON.stringify(bio) : undefined,
    })
    await refreshCurrentAccountProfile()
    showToast('个人资料已自动保存', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存失败', 'error')
  } finally {
    loading.value = false
  }
}

watch(
  () => form.full_name,
  () => {
    if (autoSaveTimer) window.clearTimeout(autoSaveTimer)
    autoSaveTimer = window.setTimeout(() => {
      if (form.full_name && authState.profile && form.full_name !== authState.profile.full_name) {
        void save()
      }
    }, 2000)
  },
)

onBeforeUnmount(() => {
  if (autoSaveTimer) window.clearTimeout(autoSaveTimer)
  if (toastTimer) window.clearTimeout(toastTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-10 dark:bg-slate-900">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[70] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
      data-testid="personal-toast"
    >
      {{ toastMessage }}
    </div>
    <div class="sticky top-0 z-10 flex items-center gap-4 bg-white px-4 py-4 shadow-sm dark:bg-slate-800">
      <button class="flex h-10 w-10 items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700" @click="router.back()">
        <ChevronLeft class="h-6 w-6" />
      </button>
      <h1 class="text-xl font-bold text-slate-900 dark:text-white">基本信息管理</h1>
    </div>

    <main class="mx-auto max-w-2xl space-y-6 p-4">
      <section class="rounded-2xl bg-white p-5 shadow-md dark:bg-slate-800">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
          <User class="h-5 w-5 text-blue-500" />
          身份信息
        </h2>
        <div class="mt-4 space-y-4">
          <label class="block space-y-2">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-200">真实姓名</span>
            <input v-model="form.full_name" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-full-name" placeholder="请输入您的姓名" />
          </label>

          <div class="space-y-2">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-200">性别</span>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <input v-model="form.gender" type="radio" value="male" />
                男
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <input v-model="form.gender" type="radio" value="female" />
                女
              </label>
            </div>
          </div>

          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <Calendar class="h-4 w-4" />
              年龄阶段
            </span>
            <select v-model="form.age" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-age">
              <option value="">选择您的年龄</option>
              <option v-for="age in ages" :key="age" :value="age">{{ age }} 岁</option>
            </select>
          </label>
        </div>
      </section>

      <section class="rounded-2xl bg-white p-5 shadow-md dark:bg-slate-800">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
          <Scale class="h-5 w-5 text-emerald-500" />
          身体数据
        </h2>
        <div class="mt-4 grid grid-cols-2 gap-4">
          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <Ruler class="h-4 w-4" />
              身高 (cm)
            </span>
            <input v-model="form.height" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-height" placeholder="175" type="number" />
          </label>
          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <Scale class="h-4 w-4" />
              体重 (kg)
            </span>
            <input v-model="form.weight" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-weight" placeholder="65" type="number" />
          </label>
        </div>
      </section>

      <section class="rounded-2xl bg-white p-5 shadow-md dark:bg-slate-800">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
          <Phone class="h-5 w-5 text-purple-500" />
          联系方式
        </h2>
        <div class="mt-4 space-y-4">
          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <Phone class="h-4 w-4" />
              手机号
            </span>
            <input v-model="form.phone" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-phone" placeholder="请输入手机号" type="tel" />
          </label>

          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <MessageSquare class="h-4 w-4" />
              微信号
            </span>
            <input v-model="form.wechat" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-wechat" placeholder="请输入微信号" />
          </label>

          <label class="block space-y-2">
            <span class="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
              <Mail class="h-4 w-4" />
              邮箱
            </span>
            <input v-model="form.email" class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-purple-100 dark:border-slate-700 dark:bg-slate-900" data-testid="personal-email" placeholder="请输入邮箱地址" type="email" />
          </label>
        </div>
      </section>

      <div class="pt-4">
        <button
          class="flex h-12 w-full items-center justify-center rounded-xl bg-blue-600 text-lg font-semibold text-white shadow-lg transition hover:bg-blue-700 disabled:opacity-60"
          data-testid="personal-save"
          :disabled="loading"
          @click="save"
        >
          {{ loading ? '正在保存...' : '立即保存' }}
          <Save class="ml-2 h-5 w-5" />
        </button>
        <p class="mt-4 text-center text-xs text-slate-400">修改将自动同步至您的健康云端档案</p>
      </div>
    </main>
  </div>
</template>
