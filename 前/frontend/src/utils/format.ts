import type { Money } from '@/types/api'

/** Decimal 可能以字符串返回，统一转数字 */
export function toNumber(v: Money | null | undefined): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

/** 金额格式：1,234.56 */
export function money(v: Money | null | undefined): string {
  return toNumber(v).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/** 千分位不带小数：用于大额数字 */
export function money0(v: Money | null | undefined): string {
  const n = toNumber(v)
  const r = n.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
  return r === '-0' ? '0' : r
}

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n)
}

/** UTC ISO → 本地时间 YYYY-MM-DD */
export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** UTC ISO → 本地时间 YYYY-MM-DD HH:mm */
export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${fmtDate(iso)} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 本地时间转 ISO（datetime-local input 值） */
export function toDatetimeLocal(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** datetime-local 值转后端可接受的 ISO 字符串 */
export function fromDatetimeLocal(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toISOString()
}

export function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function fmtPercent(n: number): string {
  if (!Number.isFinite(n)) return '0%'
  return `${Math.round(n)}%`
}

/** 防抖：返回新的防抖函数 */
export function debounce<A extends unknown[]>(fn: (...args: A) => void, wait = 300): (...args: A) => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  return (...args: A) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), wait)
  }
}
