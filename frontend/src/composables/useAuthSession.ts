import { computed, reactive, readonly } from 'vue'
import {
  getAuthState,
  loginWithPassword,
  logout,
  signupWithPassword,
  type AuthProfile,
  type AuthUser,
} from '@/lib/backend-auth'

interface AuthStore {
  initialized: boolean
  loading: boolean
  user: AuthUser | null
  profile: AuthProfile | null
}

const state = reactive<AuthStore>({
  initialized: false,
  loading: false,
  user: null,
  profile: null,
})

let initPromise: Promise<void> | null = null

async function syncAuthState() {
  const authState = await getAuthState()
  state.user = authState.session?.user || null
  state.profile = authState.profile
  state.initialized = true
}

async function ensureInitialized() {
  if (state.initialized) return
  if (!initPromise) {
    state.loading = true
    initPromise = syncAuthState()
      .catch(() => {
        state.user = null
        state.profile = null
        state.initialized = true
      })
      .finally(() => {
        state.loading = false
        initPromise = null
      })
  }
  await initPromise
}

async function signInWithUsername(usernameOrEmail: string, password: string) {
  state.loading = true
  try {
    const authState = await loginWithPassword(usernameOrEmail, password)
    state.user = authState.session?.user || null
    state.profile = authState.profile
    state.initialized = true
    return { error: null }
  } catch (error) {
    return { error: error as Error }
  } finally {
    state.loading = false
  }
}

async function signUpWithUsername(payload: {
  username: string
  password: string
  role?: 'user' | 'doctor'
  verificationCode?: string
  email?: string
  departmentId?: string
}) {
  state.loading = true
  try {
    const authState = await signupWithPassword(payload)
    state.user = authState.session?.user || null
    state.profile = authState.profile
    state.initialized = true
    return { error: null }
  } catch (error) {
    return { error: error as Error }
  } finally {
    state.loading = false
  }
}

async function refreshProfile() {
  state.loading = true
  try {
    await syncAuthState()
  } finally {
    state.loading = false
  }
}

async function signOut() {
  await logout()
  state.user = null
  state.profile = null
  state.initialized = true
}

export function useAuthSession() {
  return {
    state: readonly(state),
    isAuthenticated: computed(() => !!state.user),
    isDoctor: computed(() => state.profile?.role === 'doctor' || state.profile?.role === 'admin'),
    isAdminUser: computed(() => state.profile?.role === 'doctor' || state.profile?.role === 'admin' || state.profile?.role === 'super_admin'),
    isSuperAdmin: computed(() => state.profile?.role === 'super_admin'),
    ensureInitialized,
    signInWithUsername,
    signUpWithUsername,
    refreshProfile,
    signOut,
  }
}
