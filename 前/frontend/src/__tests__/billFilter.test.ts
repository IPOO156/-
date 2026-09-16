import { describe, expect, it } from 'vitest'
import { filterBills } from '../utils/billFilter'
import type { Bill, BillQuery } from '../types/api'

function mkBill(overrides: Partial<Bill>): Bill {
  return {
    id: 1,
    book: 1,
    type: 'expense',
    type_display: '支出',
    amount: '10.00',
    occurred_at: '2026-08-12T12:00:00Z',
    category: 1,
    category_name: '餐饮',
    category_type: 'expense',
    account: 1,
    account_name: '微信钱包',
    to_account: null,
    to_account_name: null,
    remark: '午餐麻辣烫',
    receipt_image: '',
    tags: [1],
    tag_names: ['聚餐'],
    status: 'normal',
    status_display: '正常',
    is_recurring: false,
    recurring_type: 'none',
    recurring_type_display: '无',
    recurring_next_at: null,
    created_at: '2026-08-12T12:00:00Z',
    updated_at: '2026-08-12T12:00:00Z',
    ...overrides,
  }
}

const EMPTY: BillQuery = { type: '', category: '', account: '', tag: '', start_date: '', end_date: '', keyword: '' }

const fixture = [
  mkBill({ id: 1, type: 'expense', category: 1, account: 1, tags: [1], occurred_at: '2026-08-12T12:00:00Z', remark: '午餐麻辣烫' }),
  mkBill({ id: 2, type: 'income', category: 10, account: 2, tags: [], occurred_at: '2026-08-10T12:00:00Z', remark: '发工资' }),
  mkBill({ id: 3, type: 'transfer', category: null, account: 1, to_account: 2, tags: [], occurred_at: '2026-08-11T12:00:00Z', remark: '转给支付宝' }),
]

describe('filterBills', () => {
  it('空筛选返回全部', () => {
    expect(filterBills(fixture, EMPTY)).toHaveLength(3)
  })

  it('按类型筛选', () => {
    expect(filterBills(fixture, { ...EMPTY, type: 'expense' })).toHaveLength(1)
    expect(filterBills(fixture, { ...EMPTY, type: 'transfer' }).map((b) => b.id)).toEqual([3])
  })

  it('按分类筛选', () => {
    expect(filterBills(fixture, { ...EMPTY, category: 10 }).map((b) => b.id)).toEqual([2])
  })

  it('按账户筛选时，转账账单转出或转入账户命中都算', () => {
    expect(filterBills(fixture, { ...EMPTY, account: 2 }).map((b) => b.id)).toEqual([2, 3])
  })

  it('按标签筛选', () => {
    expect(filterBills(fixture, { ...EMPTY, tag: 1 }).map((b) => b.id)).toEqual([1])
  })

  it('按开始/结束日期筛选（含边界）', () => {
    const r = filterBills(fixture, { ...EMPTY, start_date: '2026-08-11', end_date: '2026-08-12' })
    expect(r.map((b) => b.id).sort()).toEqual([1, 3])
  })

  it('按备注关键词筛选并忽略首尾空格', () => {
    expect(filterBills(fixture, { ...EMPTY, keyword: ' 麻辣烫 ' }).map((b) => b.id)).toEqual([1])
  })

  it('多条件组合生效', () => {
    const r = filterBills(fixture, { ...EMPTY, type: 'expense', category: 1, account: 1 })
    expect(r.map((b) => b.id)).toEqual([1])
  })

  it('条件互斥时返回空', () => {
    expect(filterBills(fixture, { ...EMPTY, type: 'income', category: 1 })).toHaveLength(0)
  })
})
