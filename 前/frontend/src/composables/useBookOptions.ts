import { ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { categoryApi } from '@/api/category'
import { accountApi } from '@/api/account'
import { tagApi } from '@/api/tag'
import type { Account, Category, Tag } from '@/types/api'

/** 按当前账本加载 分类/账户/标签 选项，账本切换时自动重载 */
export function useBookOptions() {
  const bookStore = useBookStore()
  const categories = ref<Category[]>([])
  const accounts = ref<Account[]>([])
  const tags = ref<Tag[]>([])
  const loading = ref(false)
  const loadedBookId = ref<number | null>(null)
  let seq = 0

  async function load(force = false): Promise<void> {
    const bookId = bookStore.currentBook?.id
    if (!bookId) return
    if (!force && loadedBookId.value === bookId) return
    const my = ++seq
    loading.value = true
    try {
      const [c, a, t] = await Promise.all([
        categoryApi.list({ book: bookId }),
        accountApi.list({ book: bookId }),
        tagApi.list({ book: bookId }),
      ])
      if (my !== seq) return
      categories.value = c
      accounts.value = a
      tags.value = t
      loadedBookId.value = bookId
    } finally {
      if (my === seq) loading.value = false
    }
  }

  watch(
    () => bookStore.currentBook?.id,
    (id) => {
      if (id && id !== loadedBookId.value) void load()
    },
  )

  return { categories, accounts, tags, loading, load }
}
