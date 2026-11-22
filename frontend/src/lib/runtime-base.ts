export function resolveApiBaseUrl() {
  const explicit = import.meta.env.DEV ? import.meta.env.VITE_API_BASE_URL : undefined
  if (typeof explicit === 'string' && explicit.trim()) {
    const normalized = explicit.trim().replace(/\/+$/, '')
    if (!isLocalBackendUrl(normalized)) {
      return normalized
    }
  }

  if (import.meta.env.DEV) {
    if (typeof window === 'undefined') {
      return localBackendUrl()
    }

    const { port } = window.location
    if (port === '5173' || port === '5174' || port === '5175' || port === '4173') {
      return localBackendUrl()
    }
  }

  if (typeof window === 'undefined') {
    return ''
  }

  const { origin, pathname } = window.location
  const firstPathSegment = pathname.split('/').filter(Boolean)[0]
  const basePath = firstPathSegment === 'chuxin-vue' ? `/${firstPathSegment}` : ''
  return `${origin}${basePath}`.replace(/\/+$/, '')
}

function isLocalBackendUrl(value: string) {
  try {
    const url = new URL(value)
    const loopbackHost = ['127', '0', '0', '1'].join('.')
    return url.hostname === 'localhost' || url.hostname === loopbackHost
  } catch {
    return false
  }
}

function localBackendUrl() {
  return `http://${['127', '0', '0', '1'].join('.')}:18080`
}
