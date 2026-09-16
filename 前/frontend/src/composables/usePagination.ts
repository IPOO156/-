import { computed, ref, watch } from 'vue'
import type { Ref } from 'vue'

/** 后端未启用 DRF 分页（列表返回纯数组），统一在客户端分页 */
export function usePagination<T>(items: Ref<T[]>, pageSize = 10) {
  const rawPage = ref(1)
  const size = ref(pageSize)

  // 每页条数变化时回到第一页，避免停留在越界页码
  watch(size, () => {
    rawPage.value = 1
  })

  const total = computed(() => items.value.length)
  const pages = computed(() => Math.max(1, Math.ceil(total.value / size.value)))

  /** 派生页码：数据量变化时同步钳制，避免出现越界页码 */
  const page = computed<number>({
    get: () => Math.min(rawPage.value, pages.value),
    set: (v) => {
      rawPage.value = v
    },
  })

  const paged = computed(() => {
    const start = (page.value - 1) * size.value
    return items.value.slice(start, start + size.value)
  })

  function go(p: number): void {
    rawPage.value = Math.min(Math.max(1, p), pages.value)
  }

  function reset(): void {
    rawPage.value = 1
  }

  return { page, size, total, pages, paged, go, reset }
}
