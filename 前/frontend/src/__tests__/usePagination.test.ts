import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { usePagination } from '../composables/usePagination'

const items25 = ref(Array.from({ length: 25 }, (_, i) => i + 1))

describe('usePagination（客户端分页）', () => {
  it('默认第 1 页，每页 10 条，共 3 页', () => {
    const p = usePagination(items25)
    expect(p.page.value).toBe(1)
    expect(p.size.value).toBe(10)
    expect(p.total.value).toBe(25)
    expect(p.pages.value).toBe(3)
    expect(p.paged.value).toHaveLength(10)
    expect(p.paged.value[0]).toBe(1)
  })

  it('go 翻页返回对应页数据', () => {
    const p = usePagination(items25)
    p.go(3)
    expect(p.page.value).toBe(3)
    expect(p.paged.value).toHaveLength(5)
    expect(p.paged.value[0]).toBe(21)
  })

  it('go 超出边界时钳制到首/尾页', () => {
    const p = usePagination(items25)
    p.go(99)
    expect(p.page.value).toBe(3)
    p.go(0)
    expect(p.page.value).toBe(1)
  })

  it('数据量缩小后自动回到合法页码', () => {
    const list = ref(Array.from({ length: 25 }, (_, i) => i + 1))
    const p = usePagination(list)
    p.go(3)
    list.value = Array.from({ length: 5 }, (_, i) => i + 1)
    expect(p.total.value).toBe(5)
    expect(p.pages.value).toBe(1)
    expect(p.page.value).toBe(1)
  })

  it('调整每页条数后分页结构随之变化', () => {
    const p = usePagination(items25)
    p.size.value = 50
    expect(p.pages.value).toBe(1)
    expect(p.paged.value).toHaveLength(25)
  })
})
