<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { statisticsApi } from '@/api/statistics'
import { ApiError } from '@/api/http'
import { fmtPercent, money, money0, todayStr, toNumber } from '@/utils/format'
import { RANGES, type RangeKey } from '@/utils/constants'
import type { AccountStat, BudgetStat, PieItem, StatsOverview, TagStat, TrendItem } from '@/types/api'
import SvgIcon from '@/components/SvgIcon.vue'
import PageHeader from '@/components/PageHeader.vue'
import TableSkeleton from '@/components/TableSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import ChartPie from '@/components/ChartPie.vue'
import ChartTrend from '@/components/ChartTrend.vue'
import ProgressBar from '@/components/ProgressBar.vue'

const bookStore = useBookStore()
const toast = useToast()

const range = ref<RangeKey>('month')
const startDate = ref('')
const endDate = ref('')
const loading = ref(false)

const overview = ref<StatsOverview | null>(null)
const pieItems = ref<PieItem[]>([])
const trendItems = ref<TrendItem[]>([])
const accountsStat = ref<AccountStat[]>([])
const budgetStat = ref<BudgetStat | null>(null)
const tagStats = ref<TagStat[]>([])

const granularity = computed<'day' | 'month'>(() => (range.value === 'year' ? 'month' : 'day'))

const dateline = computed(() => {
  const now = new Date()
  const pad = (n: number) => (n < 10 ? `0${n}` : String(n))
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
  const book = bookStore.currentBook?.name ?? ''
  const count = overview.value?.bill_count ?? 0
  return `截至 ${date} · 共 ${count} 笔记录${book ? ` · ${book}` : ''}`
})

const statsParams = computed(() => {
  const book = bookStore.currentBook?.id
  if (!book) return null
  if (range.value === 'custom') {
    if (!startDate.value || !endDate.value) return null
    return { book, range: 'custom' as const, start_date: startDate.value, end_date: endDate.value }
  }
  return { book, range: range.value }
})

let loadSeq = 0

async function loadAll(): Promise<void> {
  const params = statsParams.value
  if (!params) {
    overview.value = null
    pieItems.value = []
    trendItems.value = []
    accountsStat.value = []
    budgetStat.value = null
    tagStats.value = []
    return
  }
  const my = ++loadSeq
  loading.value = true
  try {
    const [ov, pie, trend, acc, budget, tags] = await Promise.all([
      statisticsApi.overview(params),
      statisticsApi.pie(params),
      statisticsApi.trend({ ...params, granularity: granularity.value }),
      statisticsApi.accounts({ book: params.book }),
      statisticsApi.budget({ book: params.book }),
      statisticsApi.tags(params),
    ])
    if (my !== loadSeq) return
    overview.value = ov
    pieItems.value = pie
    trendItems.value = trend
    accountsStat.value = acc
    budgetStat.value = budget
    tagStats.value = tags
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '统计数据加载失败')
  } finally {
    if (my === loadSeq) loading.value = false
  }
}

// 只监听派生参数对象（已包含账本 id），避免账本切换时同源重复触发
watch(statsParams, () => void loadAll(), { immediate: true })

function setRange(r: RangeKey): void {
  range.value = r
  if (r === 'custom' && !startDate.value) {
    startDate.value = todayStr()
    endDate.value = todayStr()
  }
}

function pickToday(): void {
  startDate.value = todayStr()
  endDate.value = todayStr()
}

function pickThisMonth(): void {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  startDate.value = `${y}-${m}-01`
  endDate.value = todayStr()
}

onMounted(pickThisMonth)
</script>

<template>
  <div class="page" style="--page-char: '算'">
    <PageHeader title="统计看板" sub="收支、趋势、预算，一览而明。" :dateline="dateline">
      <div class="range-box">
        <div class="segmented" role="tablist" aria-label="时间范围">
          <button
            v-for="r in RANGES"
            :key="r.value"
            class="segmented-item"
            :class="{ 'is-active': range === r.value }"
            @click="setRange(r.value)"
          >
            {{ r.label }}
          </button>
        </div>
        <div v-if="range === 'custom'" class="custom-range">
          <input v-model="startDate" type="date" class="input" aria-label="开始日期" />
          <span class="faint">至</span>
          <input v-model="endDate" type="date" class="input" aria-label="结束日期" />
          <button class="btn btn--ghost btn--sm" @click="pickToday">今日</button>
          <button class="btn btn--ghost btn--sm" @click="pickThisMonth">本月</button>
        </div>
      </div>
    </PageHeader>

    <EmptyState
      v-if="!bookStore.currentBook"
      icon="book"
      title="还没有账本"
      desc="创建账本后这里会展示收支统计。"
    >
      <template #action>
        <router-link to="/books" class="btn btn--primary">去创建账本</router-link>
      </template>
    </EmptyState>

    <div v-else-if="range === 'custom' && (!startDate || !endDate)" class="card custom-hint">
      请选择自定义日期范围后查看统计。
    </div>

    <template v-else>
      <TableSkeleton v-if="loading" :rows="4" />

      <template v-else>
        <div class="stat-grid">
          <div class="card stat-card ledger-lines rise" :style="{ animationDelay: '0ms' }">
            <div class="stat-card-top">
              <span class="stat-chip chip-green"><SvgIcon name="trend" :size="16" /></span>
            </div>
            <div class="stat-card-label">收入</div>
            <div class="stat-card-value money-in">¥{{ money(overview?.income_total) }}</div>
            <div class="stat-card-sub">当前时段累计收入</div>
          </div>
          <div class="card stat-card ledger-lines rise" :style="{ animationDelay: '70ms' }">
            <div class="stat-card-top">
              <span class="stat-chip chip-red"><SvgIcon name="bill" :size="16" /></span>
            </div>
            <div class="stat-card-label">支出</div>
            <div class="stat-card-value money-out">¥{{ money(overview?.expense_total) }}</div>
            <div class="stat-card-sub">当前时段累计支出</div>
          </div>
          <div class="card stat-card ledger-lines rise" :style="{ animationDelay: '140ms' }">
            <div class="stat-card-top">
              <span class="stat-chip chip-primary"><SvgIcon name="scale" :size="16" /></span>
            </div>
            <div class="stat-card-label">结余</div>
            <div
              class="stat-card-value"
              :class="toNumber(overview?.balance) >= 0 ? 'money-in' : 'money-out'"
            >
              ¥{{ money(overview?.balance) }}
            </div>
            <div class="stat-card-sub">收入 − 支出</div>
          </div>
          <div class="card stat-card ledger-lines rise" :style="{ animationDelay: '210ms' }">
            <div class="stat-card-top">
              <span class="stat-chip chip-neutral"><SvgIcon name="wallet" :size="16" /></span>
            </div>
            <div class="stat-card-label">总资产</div>
            <div class="stat-card-value">¥{{ money0(overview?.total_account_balance) }}</div>
            <div class="stat-card-sub">全部账户余额之和</div>
          </div>
        </div>

        <div class="dash-grid">
          <div class="card dash-card rise" :style="{ animationDelay: '280ms' }">
            <div class="dash-card-head">
              <h3 class="dash-card-title orn-diamond">支出分类占比</h3>
              <span class="dash-card-hint">{{ overview?.bill_count ?? 0 }} 笔账单</span>
            </div>
            <ChartPie :items="pieItems" type-label="支出" />
          </div>

          <div class="card dash-card rise" :style="{ animationDelay: '350ms' }">
            <div class="dash-card-head">
              <h3 class="dash-card-title orn-diamond">本月预算</h3>
              <span
                class="pill"
                :class="budgetStat?.book_over_budget ? 'pill--danger' : 'pill--success'"
              >
                {{ budgetStat?.book_over_budget ? '超支' : '未超支' }}
              </span>
            </div>
            <template v-if="budgetStat && toNumber(budgetStat.book_budget) > 0">
              <div class="budget-book">
                <div class="budget-book-line">
                  <span class="muted">已用 ¥{{ money(budgetStat.book_used) }} / ¥{{ money(budgetStat.book_budget) }}</span>
                  <span class="mono" :class="budgetStat.book_over_budget ? 'money-out' : 'muted'">{{ fmtPercent(budgetStat.book_percent) }}</span>
                </div>
                <ProgressBar :percent="budgetStat.book_percent" :over="budgetStat.book_over_budget" />
              </div>
              <ul v-if="budgetStat.categories.length" class="budget-cats">
                <li v-for="c in budgetStat.categories.slice(0, 6)" :key="c.category_id" class="budget-cat">
                  <span class="dot" :style="{ background: c.color || 'var(--c-border-strong)' }"></span>
                  <span class="budget-cat-name">{{ c.category_name }}</span>
                  <span
                    class="mono budget-cat-pct"
                    :class="c.over_budget ? 'money-out' : 'muted'"
                  >
                    {{ fmtPercent(c.percent) }}
                  </span>
                </li>
              </ul>
              <p v-else class="faint" style="margin-top: 12px">本月暂未设置分类预算。</p>
            </template>
            <EmptyState v-else icon="scale" title="未设置账本预算" desc="去「账本」页为账本设置月度预算。" />
          </div>

          <div class="card dash-card dash-card--wide rise" :style="{ animationDelay: '420ms' }">
            <div class="dash-card-head">
              <h3 class="dash-card-title orn-diamond">收支趋势</h3>
              <span class="dash-card-hint">{{ granularity === 'day' ? '按日' : '按月' }}</span>
            </div>
            <ChartTrend :items="trendItems" />
          </div>

          <div class="card dash-card rise" :style="{ animationDelay: '490ms' }">
            <div class="dash-card-head">
              <h3 class="dash-card-title orn-diamond">账户余额</h3>
            </div>
            <ul v-if="accountsStat.length" class="plain-list">
              <li v-for="a in accountsStat" :key="a.id" class="plain-row">
                <span class="dot" :style="{ background: a.is_active ? 'var(--c-primary)' : 'var(--c-border-strong)' }"></span>
                <span class="plain-name" :title="a.name">{{ a.name }}</span>
                <span class="mono" :class="toNumber(a.balance) >= 0 ? '' : 'money-out'">¥{{ money0(a.balance) }}</span>
              </li>
            </ul>
            <EmptyState v-else icon="wallet" title="暂无账户" desc="去「账户」页新建账户。" />
          </div>

          <div class="card dash-card rise" :style="{ animationDelay: '560ms' }">
            <div class="dash-card-head">
              <h3 class="dash-card-title orn-diamond">标签统计</h3>
              <span class="dash-card-hint">多标签会重复计入</span>
            </div>
            <ul v-if="tagStats.length" class="plain-list">
              <li v-for="(t, i) in tagStats.slice(0, 8)" :key="`tag-${t.tag_id ?? i}`" class="plain-row">
                <span class="dot" :style="{ background: t.color || 'var(--c-border-strong)' }"></span>
                <span class="plain-name">{{ t.tag_name ?? '未命名' }}</span>
                <span class="mono muted">¥{{ money0(t.total) }} · {{ t.count }} 笔</span>
              </li>
            </ul>
            <EmptyState v-else icon="tag" title="暂无标签统计" desc="记账时打上标签后这里会按标签汇总。" />
          </div>
        </div>
      </template>
    </template>
    <p class="page-aphorism">凡事预则立，不预则废。</p>
  </div>
</template>

<style scoped>
.range-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.custom-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.custom-range .input {
  width: 150px;
}

.custom-hint {
  padding: 24px;
  text-align: center;
  color: var(--c-text-secondary);
}

.stat-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.stat-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  color: var(--c-on-primary);
}

.chip-green {
  background: var(--c-success-bg);
  color: var(--c-success);
}

.chip-red {
  background: var(--c-danger-bg);
  color: var(--c-danger);
}

.chip-primary {
  background: var(--c-primary-bg);
  color: var(--c-primary);
}

.chip-neutral {
  background: var(--c-chip-neutral);
  color: var(--c-chip-neutral-ink);
}

.dash-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.dash-card {
  padding: 20px;
}

.dash-card--wide {
  grid-column: 1 / -1;
}

.dash-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.dash-card-title {
  font-size: 15px;
}

.dash-card-hint {
  font-size: 12px;
  color: var(--c-text-faint);
}

.budget-book {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.budget-book-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}

.budget-cats {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.budget-cat {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.budget-cat-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.budget-cat-pct {
  font-variant-numeric: tabular-nums;
}

.plain-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plain-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.plain-row:hover {
  background: var(--c-row-hover);
}

.plain-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .dash-grid {
    grid-template-columns: 1fr;
  }

  .dash-card--wide {
    grid-column: auto;
  }

  .range-box {
    align-items: stretch;
  }
}
</style>
