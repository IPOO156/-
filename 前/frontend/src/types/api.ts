/** 后端字段契约（对齐 后/API_DOC.md 与 bill/serializers.py） */

/** DRF DecimalField 默认以字符串返回，统计里的 python float 返回数字，统一用 Money 兜底 */
export type Money = number | string

/** DRF PageNumberPagination 分页信封（仅账单/回收站接口使用） */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type AccountType = 'cash' | 'wechat' | 'alipay' | 'bank_card' | 'credit_card'
export type CategoryType = 'expense' | 'income'
export type BillType = 'expense' | 'income' | 'transfer'
export type RecurringType = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly'

export interface Book {
  id: number
  name: string
  remark: string
  budget: Money
  cover: string
  is_archived: boolean
  is_default: boolean
  account_count: number
  bill_count: number
  created_at: string
  updated_at: string
}

export interface Account {
  id: number
  book: number
  name: string
  type: AccountType
  type_display: string
  initial_balance: Money
  balance: Money
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  book: number
  name: string
  type: CategoryType
  type_display: string
  icon: string
  color: string
  is_active: boolean
  is_default: boolean
  budget: Money
  created_at: string
  updated_at: string
}

export interface Tag {
  id: number
  book: number
  name: string
  color: string
  bill_count: number
  created_at: string
}

export interface Bill {
  id: number
  book: number
  type: BillType
  type_display: string
  amount: Money
  occurred_at: string
  category: number | null
  category_name: string | null
  category_type: string | null
  account: number
  account_name: string
  to_account: number | null
  to_account_name: string | null
  remark: string
  receipt_image: string
  tags: number[]
  tag_names: string[]
  status: string
  status_display: string
  is_recurring: boolean
  recurring_type: RecurringType
  recurring_type_display: string
  recurring_next_at: string | null
  created_at: string
  updated_at: string
}

/** 统计 */
export interface StatsOverview {
  expense_total: Money
  income_total: Money
  balance: Money
  total_budget: Money
  budget_used: Money
  budget_remaining: Money
  budget_percent: number
  total_account_balance: Money
  account_count: number
  bill_count: number
}

export interface PieItem {
  category_id: number | null
  category_name: string | null
  color: string
  total: Money
  count: number
  percent: number
}

export interface TrendItem {
  date: string
  expense: Money
  income: Money
}

export interface AccountStat {
  id: number
  name: string
  type: AccountType
  balance: Money
  is_active: boolean
  out_count: number
  in_count: number
}

export interface BudgetCategoryStat {
  category_id: number
  category_name: string
  color: string
  budget: Money
  used: Money
  remaining: Money
  percent: number
  over_budget: boolean
}

export interface BudgetStat {
  book_budget: Money
  book_used: Money
  book_remaining: Money
  book_percent: number
  book_over_budget: boolean
  categories: BudgetCategoryStat[]
}

export interface TagStat {
  tag_id: number | null
  tag_name: string | null
  color: string
  total: Money
  count: number
}

/** 认证 */
export interface TokenResult {
  token: string
}

/** 账单查询/筛选参数：对齐后端 bills 接口 query */
export interface BillQuery {
  book?: number
  type?: BillType | ''
  category?: number | ''
  account?: number | ''
  tag?: number | ''
  start_date?: string
  end_date?: string
  keyword?: string
  recurring?: boolean
  page?: number
  size?: number
  ordering?: string
}
