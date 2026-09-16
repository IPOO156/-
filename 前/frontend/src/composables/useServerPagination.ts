import { computed, ref } from 'vue'

/** 服务端分页状态：page/size 由前端驱动，total 来自后端 count，数据本体不在此切片 */
export function useServerPagination(pageSize = 20) {
  const page = ref(1)
  const size = ref(pageSize)
  const total = ref(0)

  const pages = computed(() => Math.max(1, Math.ceil(total.value / size.value)))

  function go(p: number): void {
    page.value = Math.min(Math.max(1, p), pages.value)
  }

  function setSize(v: number): void {
    size.value = v
    page.value = 1
  }

  function setTotal(v: number): void {
    total.value = v
  }

  function reset(): void {
    page.value = 1
  }

  return { page, size, total, pages, go, setSize, setTotal, reset }
}
