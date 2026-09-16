import { describe, expect, it, vi } from 'vitest'
import { debounce, fmtDate, fmtDateTime, fromDatetimeLocal, money, money0, toDatetimeLocal, toNumber } from '../utils/format'

describe('toNumber', () => {
  it('把 DRF Decimal 字符串转成数字', () => {
    expect(toNumber('32.50')).toBe(32.5)
    expect(toNumber('12000')).toBe(12000)
  })

  it('数字原样返回', () => {
    expect(toNumber(3)).toBe(3)
    expect(toNumber(0)).toBe(0)
  })

  it('空值、非法值归零', () => {
    expect(toNumber('')).toBe(0)
    expect(toNumber(null)).toBe(0)
    expect(toNumber(undefined)).toBe(0)
    expect(toNumber('abc')).toBe(0)
  })
})

describe('money / money0', () => {
  it('千分位 + 两位小数', () => {
    expect(money(1234.5)).toBe('1,234.50')
    expect(money('9999.9')).toBe('9,999.90')
  })

  it('空值显示为 0.00', () => {
    expect(money(null)).toBe('0.00')
  })

  it('money0 四舍五入为整数', () => {
    expect(money0(1234.5)).toBe('1,235')
  })
})

describe('fmtDate / fmtDateTime', () => {
  // 后端返回 UTC ISO；展示用本地时间。断言值由 Date 的本地 getter 计算，保证与运行环境一致
  const iso = '2026-08-12T12:30:00Z'
  const d = new Date(iso)
  const pad = (n: number) => (n < 10 ? `0${n}` : String(n))
  const ymd = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`

  it('格式化到 YYYY-MM-DD', () => {
    expect(fmtDate(iso)).toBe(ymd)
  })

  it('格式化到 YYYY-MM-DD HH:mm', () => {
    expect(fmtDateTime(iso)).toBe(`${ymd} ${hm}`)
  })

  it('空值显示为占位符', () => {
    expect(fmtDate(null)).toBe('—')
    expect(fmtDate('')).toBe('—')
  })
})

describe('toDatetimeLocal / fromDatetimeLocal', () => {
  it('UTC ISO 转 datetime-local（本地）再转回 ISO，取回同一时刻', () => {
    const local = toDatetimeLocal('2026-08-12T12:30:00Z')
    const back = new Date(fromDatetimeLocal(local))
    expect(back.getTime()).toBe(new Date('2026-08-12T12:30:00Z').getTime())
  })

  it('空值安全返回', () => {
    expect(toDatetimeLocal('')).toBe('')
    expect(fromDatetimeLocal('')).toBe('')
  })
})

describe('debounce', () => {
  it('等待期间多次触发只执行一次，且用最后一次参数', () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const run = debounce(fn, 300)
    run('a')
    run('b')
    run('c')
    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('c')
    vi.useRealTimers()
  })
})
