import type { BillType } from '@/types/api'

/** 账单类型 → 徽章色 */
export function billTypePill(t: BillType): string {
  if (t === 'expense') return 'pill--danger'
  if (t === 'income') return 'pill--success'
  return 'pill--primary'
}

/** 账单类型 → 金额色 */
export function billAmountClass(t: BillType): string {
  if (t === 'expense') return 'money-out'
  if (t === 'income') return 'money-in'
  return 'money-zero'
}

/** 账单类型 → 金额符号 */
export function billSign(t: BillType): string {
  if (t === 'expense') return '-'
  if (t === 'income') return '+'
  return ''
}
