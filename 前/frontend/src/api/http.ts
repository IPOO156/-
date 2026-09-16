/** 统一请求封装：Token 注入、错误归一化、{code,msg} 语义化 */

export const TOKEN_KEY = 'bill_admin_token'
export const REQUEST_TIMEOUT = 15000

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** DRF 错误体可能是 {detail}、字段错误对象、数组，统一提取为可读文案 */
function extractMessage(data: unknown, status: number): string {
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (Array.isArray(d.non_field_errors)) return d.non_field_errors.filter(Boolean).join('；')
    if (typeof d.detail === 'string') return d.detail
    if (Array.isArray(d.detail)) return d.detail.filter(Boolean).join('；')
    const msgs: string[] = []
    for (const [k, v] of Object.entries(d)) {
      if (Array.isArray(v)) msgs.push(`${k}：${v.filter(Boolean).join('、')}`)
      else if (typeof v === 'string') msgs.push(`${k}：${v}`)
    }
    if (msgs.length > 0) return msgs.join('；')
  }
  if (status === 401) return '登录已失效，请重新登录'
  if (status === 403) return '没有权限执行该操作'
  if (status === 404) return '请求的资源不存在'
  if (status >= 500) return '服务器出错了，请稍后再试'
  return `请求失败（${status}）`
}

function buildQuery(params?: object): string {
  if (!params) return ''
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    sp.append(k, String(v))
  }
  const qs = sp.toString()
  return qs ? `?${qs}` : ''
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  params?: object
  /** JSON body */
  body?: unknown
  /** 以表单编码提交（/api/token/ 需要） */
  form?: boolean
  /** 公开接口（不携带 Token） */
  skipAuth?: boolean
  /** 外部取消信号（如组件卸载时中止请求） */
  signal?: AbortSignal
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', params, body, form = false, skipAuth = false, signal: externalSignal } = opts
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token && !skipAuth) headers['Authorization'] = `Token ${token}`

  let payload: string | undefined
  if (body !== undefined) {
    if (form) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded'
      payload = new URLSearchParams(body as Record<string, string>).toString()
    } else {
      headers['Content-Type'] = 'application/json'
      payload = JSON.stringify(body)
    }
  }

  if (API_BASE.includes('ngrok')) headers['ngrok-skip-browser-warning'] = 'true'

  // 超时 + 外部取消：任一触发即中止请求
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
  const signal = externalSignal ? AbortSignal.any([externalSignal, controller.signal]) : controller.signal

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}${buildQuery(params)}`, {
      method,
      headers,
      body: payload,
      signal,
    })
  } catch {
    if (controller.signal.aborted) throw new ApiError(0, '请求超时，请稍后再试')
    if (externalSignal?.aborted) throw new ApiError(0, '请求已取消')
    throw new ApiError(0, '网络异常，请确认后端服务已启动')
  } finally {
    clearTimeout(timer)
  }

  if (!res.ok) {
    let data: unknown = null
    try {
      data = await res.json()
    } catch {
      /* 非 JSON 错误体忽略 */
    }
    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('bill_admin_username')
      window.dispatchEvent(new CustomEvent('bill:unauthorized'))
    }
    throw new ApiError(res.status, extractMessage(data, res.status))
  }

  if (res.status === 204) return null as T
  return (await res.json()) as T
}

export const http = {
  get: <T>(path: string, params?: object) => request<T>(path, { params }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { method: 'POST', body, ...opts }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
