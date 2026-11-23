<script setup lang="ts">
import { ArrowRight, LoaderCircle, LockKeyhole, Stethoscope, User } from 'lucide-vue-next'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthSession } from '@/composables/useAuthSession'
import { getDepartments } from '@/db/api'
import type { Department } from '@/types'
import ServiceMasthead from '@/components/ui/ServiceMasthead.vue'
import ServiceHero from '@/components/ui/ServiceHero.vue'
import { systemName } from '@/lib/service-preview'

type LoginRole = 'user' | 'doctor'
type AuthMode = 'login' | 'register'

const router = useRouter()
const { signInWithUsername, signUpWithUsername, state } = useAuthSession()
const mode = ref<AuthMode>('login')
const role = ref<LoginRole>('user')
const username = ref('')
const password = ref('')
const verificationCode = ref('')
const departmentId = ref('')
const departments = ref<Department[]>([])
const departmentsLoading = ref(false)
const isSubmitting = ref(false)
const toastMessage = ref('')
const toastTone = ref<'success' | 'error'>('success')
let toastTimer: number | null = null

const roleOptions = [
  { value: 'user' as const, label: '用户端', icon: User },
  { value: 'doctor' as const, label: '管理员端', icon: Stethoscope },
]

const sanitizeUsername = (value: string) => value.trim()

const validateUsername = (value: string) => {
  if (!value) return '用户名不能为空'
  if (value.length < 2) return '用户名至少需要2个字符'
  if (value.length > 20) return '用户名不能超过20个字符'
  if (!/^[\u4e00-\u9fa5a-zA-Z0-9_-]+$/.test(value)) return '用户名只能包含中文、英文、数字、下划线和连字符'
  if (/^\d+$/.test(value)) return '用户名不能为纯数字'
  if (/^[-_]|[-_]$/.test(value)) return '用户名不能以特殊字符开头或结尾'
  return ''
}

const showToast = (message: string, tone: 'success' | 'error' = 'success') => {
  toastMessage.value = message
  toastTone.value = tone
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, 2200)
}

onBeforeUnmount(() => {
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
  }
})

const loadDepartments = async () => {
  departmentsLoading.value = true
  try {
    departments.value = (await getDepartments(false)).filter((item) => item.status === 'active')
    const onlyDepartment = departments.value.length === 1 ? departments.value[0] : null
    if (!departmentId.value && onlyDepartment) {
      departmentId.value = onlyDepartment.id
    }
  } catch (error) {
    showToast(error instanceof Error ? `部门加载失败: ${error.message}` : '部门加载失败', 'error')
  } finally {
    departmentsLoading.value = false
  }
}

onMounted(loadDepartments)

async function submitAuth() {
  const cleanedUsername = sanitizeUsername(username.value)
  toastMessage.value = ''

  if (mode.value === 'login') {
    if (!cleanedUsername || !password.value) {
      showToast('请输入用户名和密码', 'error')
      return
    }
    if (role.value === 'doctor' && password.value.length < 6) {
      showToast('管理员端密码至少需要6个字符', 'error')
      return
    }
  } else {
    const usernameError = validateUsername(cleanedUsername)
    if (usernameError) {
      showToast(usernameError, 'error')
      return
    }
    if (!password.value) {
      showToast('请输入密码', 'error')
      return
    }
    if (password.value.length < 6) {
      showToast('密码至少需要6个字符', 'error')
      return
    }
    if (role.value === 'doctor' && !verificationCode.value.trim()) {
      showToast('管理员端注册需要验证码', 'error')
      return
    }
    if (role.value === 'user' && !departmentId.value) {
      showToast('请选择所属部门', 'error')
      return
    }
  }

  isSubmitting.value = true

  try {
    if (mode.value === 'login') {
      const { error } = await signInWithUsername(cleanedUsername, password.value)
      if (error) {
        showToast(`登录失败: ${error.message || '请检查账号和密码。'}`, 'error')
        return
      }
    } else {
      const { error } = await signUpWithUsername({
        username: cleanedUsername,
        password: password.value,
        role: role.value === 'doctor' ? 'doctor' : 'user',
        verificationCode: role.value === 'doctor' ? verificationCode.value.trim() : undefined,
        departmentId: role.value === 'user' ? departmentId.value : undefined,
      })
      if (error) {
        showToast(`注册失败: ${error.message || '请检查填写信息。'}`, 'error')
        return
      }
    }

    const stateFrom = typeof window.history.state?.from === 'string' ? window.history.state.from : null
    const from = stateFrom || '/'
    const safeUserRedirect = from.startsWith('/admin') || from.startsWith('/doctor') || from.startsWith('/super-admin') ? '/' : from
    if (state.profile?.role === 'super_admin') {
      showToast('管理员后台登录成功')
      await router.replace('/admin/dashboard')
    } else if (state.profile?.role === 'doctor' || state.profile?.role === 'admin') {
      showToast(mode.value === 'register' ? '注册成功,正在登录...' : '管理员端登录成功')
      await router.replace('/admin/dashboard')
    } else {
      showToast(mode.value === 'register' ? '注册成功,正在登录...' : '登录成功')
      await router.replace(safeUserRedirect)
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : '无法连接后端服务，请确认后端已启动。', 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="service-page">
    <ServiceMasthead />
    <ServiceHero variant="full" :title="systemName" eyebrow="高原身心健康研究" />
    <main class="service-width py-5 sm:py-7">
    <div
      v-if="toastMessage"
      class="fixed left-1/2 top-[72px] z-[80] -translate-x-1/2 rounded-full px-4 py-2 text-sm font-semibold text-white shadow-xl"
      :class="toastTone === 'error' ? 'bg-rose-600 shadow-rose-900/20' : 'bg-emerald-600 shadow-emerald-900/20'"
      data-testid="login-toast"
      role="status"
    >
      {{ toastMessage }}
    </div>

    <div class="service-card service-card-highlight mx-auto max-w-[460px]">
      <div class="flex items-center gap-3 border-b px-5 py-5 sm:px-7">
        <span class="service-icon"><LockKeyhole aria-hidden="true" /></span>
        <h2 class="text-xl font-bold">{{ mode === 'login' ? '账号登录' : '账号注册' }}</h2>
      </div>

      <div class="px-5 pb-6 pt-5 sm:px-7">
        <label class="mb-2 inline-block text-sm font-medium text-slate-700 dark:text-slate-200">登录角色</label>
        <div class="service-segment mb-4 grid grid-cols-2 gap-2">
          <button
            v-for="item in roleOptions"
            :key="item.value"
            class="flex items-center justify-center gap-2 rounded-[6px] px-4 py-2.5 text-sm font-semibold transition"
            :aria-pressed="role === item.value"
            :data-testid="`role-${item.value}`"
            type="button"
            @click="role = item.value"
          >
            <component :is="item.icon" class="h-4 w-4" />
            {{ item.label }}
          </button>
        </div>

        <div class="service-segment mb-5 grid grid-cols-2 gap-2">
          <button
            class="rounded-[6px] px-4 py-2.5 text-sm font-semibold transition"
            :aria-pressed="mode === 'login'"
            data-testid="mode-login"
            type="button"
            @click="mode = 'login'"
          >
            登录
          </button>
          <button
            class="rounded-[6px] px-4 py-2.5 text-sm font-semibold transition"
            :aria-pressed="mode === 'register'"
            data-testid="mode-register"
            type="button"
            @click="mode = 'register'"
          >
            注册
          </button>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="submitAuth">
          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-200" for="login-username">用户名</label>
            <input
              id="login-username"
              v-model="username"
              autocomplete="username"
              class="w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-base outline-none transition focus:ring-2 focus:ring-primary/20 dark:border-slate-800 md:text-sm"
              data-testid="username-input"
              maxlength="20"
              :placeholder="mode === 'register' ? '支持中文、英文、数字（2-20个字符）' : role === 'doctor' ? '请输入管理员账号用户名' : '请输入用户名'"
              type="text"
            />
            <p v-if="mode === 'register'" class="text-xs text-slate-500">
              可使用中文昵称，支持中文、英文、数字、下划线和连字符
            </p>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-200" for="login-password">密码</label>
            <input
              id="login-password"
              v-model="password"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              class="w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-base outline-none transition focus:ring-2 focus:ring-primary/20 dark:border-slate-800 md:text-sm"
              data-testid="password-input"
              :placeholder="mode === 'register' ? '至少6个字符' : role === 'doctor' ? '管理员端至少6位密码' : '请输入密码'"
              type="password"
            />
          </div>

          <div v-if="mode === 'register' && role === 'doctor'" class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-200" for="verification-code">验证码</label>
            <input
              id="verification-code"
              v-model="verificationCode"
              class="w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-base outline-none transition focus:ring-2 focus:ring-primary/20 dark:border-slate-800 md:text-sm"
              data-testid="verification-code-input"
              placeholder="请输入管理员端验证码"
              type="text"
            />
            <p class="text-xs text-slate-500">管理员端注册需要验证码，请联系管理员获取</p>
          </div>

          <div v-if="mode === 'register' && role === 'user'" class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-200" for="department-id">所属部门</label>
            <select
              id="department-id"
              v-model="departmentId"
              class="w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-base outline-none transition focus:ring-2 focus:ring-primary/20 dark:border-slate-800 md:text-sm"
              data-testid="department-select"
              :disabled="departmentsLoading"
            >
              <option value="">{{ departmentsLoading ? '正在加载部门...' : '请选择所属部门' }}</option>
              <option v-for="department in departments" :key="department.id" :value="department.id">
                {{ department.name }}
              </option>
            </select>
            <p class="text-xs text-slate-500">所属部门由超级管理员维护，注册后管理员可按部门发布任务</p>
          </div>

          <button
            class="service-button w-full"
            :disabled="isSubmitting"
            type="submit"
          >
            <span class="inline-flex items-center gap-2">
              <LoaderCircle v-if="isSubmitting" class="h-4 w-4 animate-spin" aria-hidden="true" />
              <ArrowRight v-else aria-hidden="true" />
              {{ isSubmitting ? (mode === 'login' ? '登录中' : '注册中') : (mode === 'login' ? '登录' : '注册') }}
            </span>
          </button>
        </form>
      </div>
    </div>
    </main>
  </div>
</template>
