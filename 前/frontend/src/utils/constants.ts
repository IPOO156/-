import type { AccountType, BillType, CategoryType, RecurringType } from '@/types/api'

export interface Option<T extends string = string> {
  value: T
  label: string
}

export const ACCOUNT_TYPES: Option<AccountType>[] = [
  { value: 'cash', label: '现金' },
  { value: 'wechat', label: '微信' },
  { value: 'alipay', label: '支付宝' },
  { value: 'bank_card', label: '银行卡' },
  { value: 'credit_card', label: '信用卡' },
]

export const CATEGORY_TYPES: Option<CategoryType>[] = [
  { value: 'expense', label: '支出' },
  { value: 'income', label: '收入' },
]

export const BILL_TYPES: Option<BillType>[] = [
  { value: 'expense', label: '支出' },
  { value: 'income', label: '收入' },
  { value: 'transfer', label: '转账' },
]

export const RECURRING_TYPES: Option<RecurringType>[] = [
  { value: 'none', label: '无' },
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'yearly', label: '每年' },
]

export type RangeKey = 'today' | 'week' | 'month' | 'year' | 'custom'

export const RANGES: Option<RangeKey>[] = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'year', label: '本年' },
  { value: 'custom', label: '自定义' },
]

export const CATEGORY_COLORS = [
  '#b45a0b',
  '#256e47',
  '#a63a2b',
  '#8a6d3b',
  '#5b6e8c',
  '#7a5c94',
  '#3d7a74',
  '#b06a3c',
  '#6b624f',
  '#8c5a7a',
]

export const DEFAULT_EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '住房', '娱乐', '医疗', '学习', '人情', '其他']
export const DEFAULT_INCOME_CATEGORIES = ['工资', '红包', '兼职', '理财收益', '其他收入']
