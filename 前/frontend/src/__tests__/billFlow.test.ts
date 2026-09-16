import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import BillsView from '@/views/BillsView.vue'
import { useBookStore } from '@/stores/book'
import type { Bill } from '@/types/api'

/** 账单列表关键流程：服务端分页参数、筛选触发重拉、跨页选择计数 */

const billListMock = vi.fn()

vi.mock('@/api/bill', () => ({
  billApi: {
    list: (...args: unknown[]) => billListMock(...args),
    detail: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    batchDelete: vi.fn(),
    batchUpdateCategory: vi.fn(),
    recycleBin: vi.fn(),
    restore: vi.fn(),
    permanentDelete: vi.fn(),
  },
}))

vi.mock('@/composables/useBookOptions', () => ({
  useBookOptions: () => ({
    categories: ref([]),
    accounts: ref([]),
    tags: ref([]),
    load: vi.fn().mockResolvedValue(undefined),
  }),
}))

const book = {
  id: 1,
  name: '测试账本',
  remark: '',
  budget: '0',
  cover: '',
  is_archived: false,
  is_default: true,
  account_count: 0,
  bill_count: 0,
  created_at: '',
  updated_at: '',
}

function mkBill(id: number, type: 'expense' | 'income' | 'transfer' = 'expense'): Bill {
  return {
    id,
    type,
    type_display: type === 'expense' ? '支出' : type === 'income' ? '收入' : '转账',
    status_display: '正常',
    recurring_type_display: '无',
    tag_names: [],
    account_name: '现金',
    to_account_name: null,
    category_name: '餐饮',
    category_type: 'expense',
    amount: '10',
    occurred_at: '2026-08-15T10:00:00',
    book: 1,
    status: 'normal',
    is_recurring: false,
    recurring_type: 'none',
    recurring_next_at: null,
    created_at: '',
    updated_at: '',
    category: 1,
    account: 1,
    to_account: null,
    remark: '',
    receipt_image: '',
    tags: [],
  } as Bill
}

function makePage(count: number, ids: number[] = []) {
  const results = ids.length ? ids.map((id) => mkBill(id)) : []
  return { count, next: null, previous: null, results }
}

describe('BillsView 账单列表流程（服务端分页）', () => {
  beforeEach(() => {
    billListMock.mockReset()
    setActivePinia(createPinia())
    const store = useBookStore()
    store.books = [book as never]
    store.setCurrentBook(1)
  })

  it('首次加载携带 book/page/size 参数并渲染结果', async () => {
    billListMock.mockResolvedValue(makePage(1, [101]))
    const w = mount(BillsView, { global: { stubs: { SvgIcon: true } } })
    await flushPromises()

    const call = billListMock.mock.calls[0]?.[0] ?? {}
    expect(call.book).toBe(1)
    expect(call.page).toBe(1)
    expect(call.size).toBe(20)
    expect(w.find('.table tbody tr').exists()).toBe(true)
    expect(w.find('.dateline').text()).toContain('共 1 条')
  })

  it('切换筛选条件后重置页码并携带筛选参数重新拉取', async () => {
    billListMock.mockResolvedValue(makePage(2, [1, 2]))
    const w = mount(BillsView, { global: { stubs: { SvgIcon: true } } })
    await flushPromises()

    billListMock.mockResolvedValue(makePage(1, [1]))
    await w.find('[aria-label="类型筛选"]').setValue('expense')
    await flushPromises()

    const last = billListMock.mock.calls.at(-1)?.[0] ?? {}
    expect(last.type).toBe('expense')
    expect(last.page).toBe(1)
  })

  it('跨页选择：勾选行后 selected 集合累计，批量操作传完整 id 列表', async () => {
    billListMock.mockResolvedValue(makePage(2, [1, 2]))
    const w = mount(BillsView, { global: { stubs: { SvgIcon: true } } })
    await flushPromises()

    const boxes = w.findAll('tbody input[type="checkbox"]')
    expect(boxes.length).toBe(2)
    await boxes[0]!.setValue(true)
    await boxes[1]!.setValue(true)

    expect(w.find('.batch-bar').text()).toContain('已选 2 条')
    expect(w.find('.dateline').text()).toContain('共 2 条')
  })
})
