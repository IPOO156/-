import { http } from './http'
import type {
  AccountStat,
  BudgetStat,
  PieItem,
  StatsOverview,
  TagStat,
  TrendItem,
} from '@/types/api'
import type { RangeKey } from '@/utils/constants'

export interface StatsParams {
  book?: number
  range?: RangeKey
  start_date?: string
  end_date?: string
}

export const statisticsApi = {
  overview: (params: StatsParams) => http.get<StatsOverview>('/statistics/overview/', params),
  pie: (params: StatsParams & { type?: 'expense' | 'income' }) =>
    http.get<PieItem[]>('/statistics/pie/', params),
  trend: (params: StatsParams & { granularity?: 'day' | 'month' }) =>
    http.get<TrendItem[]>('/statistics/trend/', params),
  accounts: (params: { book?: number }) => http.get<AccountStat[]>('/statistics/accounts/', params),
  budget: (params: { book?: number }) => http.get<BudgetStat>('/statistics/budget/', params),
  tags: (params: StatsParams) => http.get<TagStat[]>('/statistics/tags/', params),
}
