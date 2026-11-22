import { resolveApiBaseUrl } from '@/lib/runtime-base'

const TOKEN_KEY = 'chuxin.access-token'
const SESSION_EVENT = 'chuxin:session-changed'

export interface AuthUser {
  id: string
  email?: string
  user_metadata?: {
    username?: string
    role?: string
  }
}

export interface AuthProfile {
  id: string
  username: string
  email?: string | null
  phone?: string | null
  wechat?: string | null
  role: 'user' | 'doctor' | 'admin' | 'super_admin'
  department_id?: string | null
  department_name?: string | null
  department_status?: string | null
  avatar_url?: string | null
  full_name?: string | null
  gender?: string | null
  birth_date?: string | null
  bio?: string | null
  background_url?: string | null
  selected_background?: string | null
  created_at?: string
  updated_at?: string
}

export interface AppSession {
  access_token: string
  user: AuthUser
}

export interface AuthState {
  session: AppSession | null
  profile: AuthProfile | null
}

interface SessionEnvelope {
  accessToken?: string | null
  user?: AuthUser | null
  profile?: AuthProfile | null
}

function buildUrl(path: string) {
  const base = resolveApiBaseUrl()
  return new URL(`${base}${path.startsWith('/') ? path : `/${path}`}`, window.location.origin).toString()
}

function readToken() {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(TOKEN_KEY)
}

function writeToken(token: string | null) {
  if (typeof window === 'undefined') return

  const previous = window.localStorage.getItem(TOKEN_KEY)
  if ((previous || null) === token) return

  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token)
  } else {
    window.localStorage.removeItem(TOKEN_KEY)
  }
  window.dispatchEvent(new CustomEvent(SESSION_EVENT))
}

function authHeaders(token = readToken()) {
  const headers: Record<string, string> = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

async function parseJson(response: Response) {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function resolveErrorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === 'object' && 'error' in payload) {
    const error = (payload as { error?: unknown }).error
    if (typeof error === 'string' && error.trim()) {
      return error
    }
  }
  return fallback
}

function envelopeToAuthState(envelope: SessionEnvelope | null | undefined): AuthState {
  const accessToken = envelope?.accessToken || null
  const user = envelope?.user || null
  return {
    session: accessToken && user ? { access_token: accessToken, user } : null,
    profile: envelope?.profile || null,
  }
}

export function getAccessToken() {
  return readToken()
}

export function subscribeAuthStateChange(callback: () => void) {
  if (typeof window === 'undefined') {
    return () => {}
  }

  const handler = () => callback()
  window.addEventListener(SESSION_EVENT, handler)
  window.addEventListener('storage', handler)

  return () => {
    window.removeEventListener(SESSION_EVENT, handler)
    window.removeEventListener('storage', handler)
  }
}

export async function getAuthState(): Promise<AuthState> {
  const response = await fetch(buildUrl('/api/auth/session'), {
    headers: {
      Accept: 'application/json',
      ...authHeaders(),
    },
  })
  const payload = await parseJson(response)
  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, '获取登录状态失败'))
  }

  const body = payload as { session?: AppSession | null; profile?: AuthProfile | null }
  if (!body.session?.access_token) {
    writeToken(null)
    return { session: null, profile: null }
  }

  writeToken(body.session.access_token)
  return { session: body.session, profile: body.profile || null }
}

export async function loginWithPassword(usernameOrEmail: string, password: string): Promise<AuthState> {
  const response = await fetch(buildUrl('/api/auth/login'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ usernameOrEmail, password }),
  })
  const payload = await parseJson(response)
  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, '登录失败'))
  }

  const state = envelopeToAuthState(payload as SessionEnvelope)
  writeToken(state.session?.access_token || null)
  return state
}

export async function signupWithPassword(payload: {
  username: string
  password: string
  role?: 'user' | 'doctor'
  verificationCode?: string
  email?: string
  departmentId?: string
}): Promise<AuthState> {
  const response = await fetch(buildUrl('/api/auth/signup'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  })
  const body = await parseJson(response)
  if (!response.ok) {
    throw new Error(resolveErrorMessage(body, '注册失败'))
  }

  const state = envelopeToAuthState(body as SessionEnvelope)
  writeToken(state.session?.access_token || null)
  return state
}

export async function logout() {
  const token = readToken()
  writeToken(null)
  if (!token) return

  try {
    await fetch(buildUrl('/api/auth/logout'), {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        ...authHeaders(token),
      },
    })
  } catch {
    // Ignore local sign-out network errors.
  }
}
