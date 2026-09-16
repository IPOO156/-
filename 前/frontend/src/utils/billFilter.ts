import type { Bill, BillQuery } from '@/types/api'
import { fmtDate } from '@/utils/format'

/** 记账列表客户端筛选（纯函数，便于单测） */
export function filterBills(bills: Bill[], q: BillQuery): Bill[] {
  const kw = q.keyword?.trim() ?? ''
  return bills.filter((b) => {
    if (q.type && b.type !== q.type) return false
    if (q.category !== '' && q.category !== undefined && b.category !== q.category) return false
    if (q.account !== '' && q.account !== undefined && b.account !== q.account && b.to_account !== q.account)
      return false
    if (q.tag !== '' && q.tag !== undefined && !b.tags.includes(q.tag)) return false
    const day = fmtDate(b.occurred_at)
    if (q.start_date && day < q.start_date) return false
    if (q.end_date && day > q.end_date) return false
    if (kw && !b.remark.includes(kw)) return false
    return true
  })
}
