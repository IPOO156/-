import { http } from './http'
import type { Bill, BillQuery, BillType, Paginated } from '@/types/api'

export interface BillPayload {
  book: number
  type: BillType
  amount: number
  /** 后端 occurred_at 为 auto_now_add，提交被忽略，故可选 */
  occurred_at?: string
  category: number | null
  account: number
  to_account: number | null
  remark: string
  tags: number[]
}

export const billApi = {
  list: (params?: BillQuery) => http.get<Paginated<Bill>>('/bills/', params),
  detail: (id: number) => http.get<Bill>(`/bills/${id}/`),
  create: (data: BillPayload) => http.post<Bill>('/bills/', data),
  update: (id: number, data: Partial<BillPayload>) => http.put<Bill>(`/bills/${id}/`, data),
  remove: (id: number) => http.delete<Bill>(`/bills/${id}/`),
  batchDelete: (ids: number[]) => http.post<{ deleted_count: number }>('/bills/batch_delete/', { ids }),
  batchUpdateCategory: (ids: number[], category_id: number) =>
    http.post<{ updated_count: number }>('/bills/batch_update_category/', { ids, category_id }),
  recycleBin: (params?: BillQuery) => http.get<Paginated<Bill>>('/bills/recycle_bin/', params),
  restore: (id: number) => http.post<Bill>(`/bills/${id}/restore/`),
  permanentDelete: (id: number) => http.post<{ detail: string }>(`/bills/${id}/permanent_delete/`),
}
