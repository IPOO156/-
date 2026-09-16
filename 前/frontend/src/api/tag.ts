import { http } from './http'
import type { Tag } from '@/types/api'

export interface TagPayload {
  book: number
  name: string
  color: string
}

export const tagApi = {
  list: (params?: { book?: number }) => http.get<Tag[]>('/tags/', params),
  create: (data: TagPayload) => http.post<Tag>('/tags/', data),
  update: (id: number, data: Partial<TagPayload>) => http.put<Tag>(`/tags/${id}/`, data),
  remove: (id: number) => http.delete<Tag>(`/tags/${id}/`),
}
