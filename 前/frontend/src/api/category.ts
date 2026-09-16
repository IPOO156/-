import { http } from './http'
import type { Category, CategoryType } from '@/types/api'

export interface CategoryPayload {
  book: number
  name: string
  type: CategoryType
  color: string
  icon: string
  budget: number
}

export const categoryApi = {
  list: (params?: { book?: number; type?: CategoryType; active?: boolean }) =>
    http.get<Category[]>('/categories/', params),
  create: (data: CategoryPayload) => http.post<Category>('/categories/', data),
  update: (id: number, data: Partial<CategoryPayload>) => http.put<Category>(`/categories/${id}/`, data),
  remove: (id: number) => http.delete<Category>(`/categories/${id}/`),
  disable: (id: number) => http.post<Category>(`/categories/${id}/disable/`),
  enable: (id: number) => http.post<Category>(`/categories/${id}/enable/`),
}
