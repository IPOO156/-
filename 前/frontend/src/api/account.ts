import { http } from './http'
import type { Account, AccountType, Bill } from '@/types/api'

export interface AccountPayload {
  book: number
  name: string
  type: AccountType
  initial_balance: number
}

export interface TransferPayload {
  from_account: number
  to_account: number
  amount: number
  remark?: string
}

export const accountApi = {
  list: (params?: { book?: number; active?: boolean }) => http.get<Account[]>('/accounts/', params),
  create: (data: AccountPayload) => http.post<Account>('/accounts/', data),
  update: (id: number, data: Partial<AccountPayload>) => http.put<Account>(`/accounts/${id}/`, data),
  remove: (id: number) => http.delete<Account>(`/accounts/${id}/`),
  disable: (id: number) => http.post<Account>(`/accounts/${id}/disable/`),
  enable: (id: number) => http.post<Account>(`/accounts/${id}/enable/`),
  transfer: (data: TransferPayload) => http.post<Bill>('/accounts/transfer/', data),
}
