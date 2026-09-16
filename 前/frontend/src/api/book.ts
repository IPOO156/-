import { http } from './http'
import type { Book } from '@/types/api'

export interface BookPayload {
  name: string
  remark: string
  budget: number
  cover: string
}

export const bookApi = {
  list: (params?: { archived?: boolean }) => http.get<Book[]>('/books/', params),
  create: (data: BookPayload) => http.post<Book>('/books/', data),
  update: (id: number, data: BookPayload) => http.put<Book>(`/books/${id}/`, data),
  remove: (id: number) => http.delete<Book>(`/books/${id}/`),
  archive: (id: number) => http.post<Book>(`/books/${id}/archive/`),
  unarchive: (id: number) => http.post<Book>(`/books/${id}/unarchive/`),
  setDefault: (id: number) => http.post<Book>(`/books/${id}/set_default/`),
}
