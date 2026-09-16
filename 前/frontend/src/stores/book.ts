import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { bookApi } from '@/api/book'
import type { Book } from '@/types/api'

/** 每个账号记住各自默认账本，避免串号 */
function currentBookKey(): string {
  return `bill_admin_current_book_${localStorage.getItem('bill_admin_username') ?? ''}`
}

export const useBookStore = defineStore('book', () => {
  const books = ref<Book[]>([])
  const loaded = ref(false)
  const currentBookId = ref<number | null>(Number(localStorage.getItem(currentBookKey())) || null)

  const currentBook = computed<Book | null>(
    () =>
      books.value.find((b) => b.id === currentBookId.value) ??
      books.value.find((b) => b.is_default) ??
      books.value[0] ??
      null,
  )

  async function fetchBooks(force = false): Promise<void> {
    if (loaded.value && !force) return
    books.value = await bookApi.list()
    loaded.value = true
    if (currentBook.value) {
      currentBookId.value = currentBook.value.id
      localStorage.setItem(currentBookKey(), String(currentBook.value.id))
    }
  }

  function setCurrentBook(id: number): void {
    currentBookId.value = id
    localStorage.setItem(currentBookKey(), String(id))
  }

  /** 登出/换账号登录时清空，强制重新拉取当前账号数据 */
  function reset(): void {
    books.value = []
    loaded.value = false
    currentBookId.value = null
  }

  /** 增删改后同步列表缓存 */
  function sync(book: Book): void {
    const idx = books.value.findIndex((b) => b.id === book.id)
    if (idx >= 0) books.value[idx] = book
    else books.value.unshift(book)
    if (book.is_default) {
      books.value.forEach((b) => {
        if (b.id !== book.id) b.is_default = false
      })
    }
  }

  function remove(id: number): void {
    books.value = books.value.filter((b) => b.id !== id)
    if (currentBookId.value === id) currentBookId.value = null
  }

  return { books, loaded, currentBookId, currentBook, fetchBooks, setCurrentBook, sync, remove, reset }
})
