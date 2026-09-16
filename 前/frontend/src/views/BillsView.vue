<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { useServerPagination } from '@/composables/useServerPagination'
import { useBookOptions } from '@/composables/useBookOptions'
import { billApi } from '@/api/bill'
import { ApiError } from '@/api/http'
import { debounce, fmtDateTime, money } from '@/utils/format'
import { billAmountClass, billSign, billTypePill } from '@/utils/billType'
import { BILL_TYPES } from '@/utils/constants'
import type { Bill, BillQuery, BillType, Category } from '@/types/api'
import SvgIcon from '@/components/SvgIcon.vue'
import PageHeader from '@/components/PageHeader.vue'
import TableSkeleton from '@/components/TableSkeleton.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import BaseModal from '@/components/BaseModal.vue'
import BillFormModal from '@/components/BillFormModal.vue'

const bookStore = useBookStore()
const toast = useToast()
const { categories: optionCategories, accounts: optionAccounts, tags: optionTags, load: reloadOptions } =
  useBookOptions()

/* ---------- 列表与服务端分页 ---------- */
const bills = ref<Bill[]>([])
const loading = ref(false)
const { page, size, total, pages, go, setSize, setTotal, reset } = useServerPagination(20)

const filters = reactive<BillQuery>({
  type: '',
  category: '',
  account: '',
  tag: '',
  start_date: '',
  end_date: '',
  keyword: '',
})

const keywordDebounced = ref('')
watch(
  () => filters.keyword,
  debounce((v: string | undefined) => {
    keywordDebounced.value = (v ?? '').trim()
  }, 300),
)

/** 组装服务端查询参数：空值由 http.buildQuery 丢弃 */
function buildServerQuery(): BillQuery {
  return {
    book: bookStore.currentBook?.id,
    type: filters.type || undefined,
    category: filters.category === '' ? undefined : filters.category,
    account: filters.account === '' ? undefined : filters.account,
    tag: filters.tag === '' ? undefined : filters.tag,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    keyword: keywordDebounced.value || undefined,
    page: page.value,
    size: size.value,
  }
}

function resetFilters(): void {
  Object.assign(filters, { type: '', category: '', account: '', tag: '', start_date: '', end_date: '', keyword: '' })
}

/* ---------- 行选择（跨页保留 id 集合与类型，供批量操作使用） ---------- */
const selected = ref<Set<number>>(new Set())
const selectedTypes = ref<Map<number, BillType>>(new Map())

function toggleRow(b: Bill): void {
  const next = new Set(selected.value)
  const nextTypes = new Map(selectedTypes.value)
  if (next.has(b.id)) {
    next.delete(b.id)
    nextTypes.delete(b.id)
  } else {
    next.add(b.id)
    nextTypes.set(b.id, b.type)
  }
  selected.value = next
  selectedTypes.value = nextTypes
}

function clearSelection(): void {
  if (selected.value.size > 0) {
    selected.value = new Set()
    selectedTypes.value = new Map()
  }
}

const allChecked = computed(() => bills.value.length > 0 && bills.value.every((b) => selected.value.has(b.id)))
const someChecked = computed(() => bills.value.some((b) => selected.value.has(b.id)))

function togglePage(): void {
  const next = new Set(selected.value)
  const nextTypes = new Map(selectedTypes.value)
  if (allChecked.value) {
    bills.value.forEach((b) => {
      next.delete(b.id)
      nextTypes.delete(b.id)
    })
  } else {
    bills.value.forEach((b) => {
      next.add(b.id)
      nextTypes.set(b.id, b.type)
    })
  }
  selected.value = next
  selectedTypes.value = nextTypes
}

/* ---------- 数据加载 ---------- */
let loadSeq = 0

async function loadData(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId) return
  const my = ++loadSeq
  loading.value = true
  try {
    const res = await billApi.list(buildServerQuery())
    if (my !== loadSeq) return
    bills.value = res.results
    setTotal(res.count)
    // 筛选/删除后当前页变空且非第一页 → 回落到上一页
    if (res.results.length === 0 && page.value > 1) {
      go(page.value - 1)
      void loadData()
      return
    }
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '账单加载失败')
  } finally {
    if (my === loadSeq) loading.value = false
  }
  try {
    await reloadOptions()
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '分类/账户/标签加载失败')
  }
}

/** 筛选条件变化 → 重置到第一页并重新拉取 */
watch(
  [
    () => filters.type,
    () => filters.category,
    () => filters.account,
    () => filters.tag,
    () => filters.start_date,
    () => filters.end_date,
    keywordDebounced,
  ],
  () => {
    reset()
    clearSelection()
    void loadData()
  },
)

watch(
  () => bookStore.currentBook?.id,
  () => {
    selected.value = new Set()
    selectedTypes.value = new Map()
    reset()
    void loadData()
  },
  { immediate: true },
)

function onPageChange(p: number): void {
  go(p)
  void loadData()
}

function onSizeChange(v: number): void {
  setSize(v)
  void loadData()
}

/* ---------- 新增 / 编辑弹窗 ---------- */
const modalOpen = ref(false)
const isEdit = ref(false)
const editingBill = ref<Bill | null>(null)

function openCreate(): void {
  isEdit.value = false
  editingBill.value = null
  modalOpen.value = true
}

function openEdit(row: Bill): void {
  isEdit.value = true
  editingBill.value = row
  modalOpen.value = true
}

function onSaved(): void {
  modalOpen.value = false
  clearSelection()
  void loadData()
}

/* ---------- 删除（单个 / 批量） ---------- */
const deleting = ref<Bill | null>(null)
const deleteLoading = ref(false)

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await billApi.remove(deleting.value.id)
    await loadData()
    toast.success('账单已移入回收站，余额已回滚')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const batchDeleteConfirm = ref(false)
const batchDeleting = ref(false)

async function confirmBatchDelete(): Promise<void> {
  if (selected.value.size === 0 || batchDeleting.value) return
  batchDeleting.value = true
  try {
    const res = await billApi.batchDelete([...selected.value])
    await loadData()
    clearSelection()
    batchDeleteConfirm.value = false
    toast.success(`已删除 ${res.deleted_count} 条账单`)
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '批量删除失败')
  } finally {
    batchDeleting.value = false
  }
}

/* ---------- 批量修改分类 ---------- */
const batchCatOpen = ref(false)
const batchCatValue = ref<number | ''>('')
const batchCatSaving = ref(false)

const expenseCats = computed(() => optionCategories.value.filter((c) => c.type === 'expense'))
const incomeCats = computed(() => optionCategories.value.filter((c) => c.type === 'income'))

/** 按所选账单类型收敛可选项，避免收入分类被赋给支出账单（跨页时读 selectedTypes） */
const selectedType = computed<BillType | 'mixed' | null>(() => {
  if (selected.value.size === 0) return null
  const types = new Set<BillType>()
  selectedTypes.value.forEach((t) => types.add(t))
  return types.size === 1 ? types.values().next().value! : 'mixed'
})

const batchCatOptions = computed(() => {
  if (selectedType.value === 'expense') return { expense: expenseCats.value, income: [] as Category[] }
  if (selectedType.value === 'income') return { expense: [] as Category[], income: incomeCats.value }
  return { expense: expenseCats.value, income: incomeCats.value }
})

const selectedTypeLabel = computed(() => {
  if (selectedType.value === 'expense') return '支出'
  if (selectedType.value === 'income') return '收入'
  return '混合类型'
})

function openBatchCategory(): void {
  batchCatValue.value = ''
  batchCatOpen.value = true
}

async function confirmBatchCategory(): Promise<void> {
  if (batchCatValue.value === '' || batchCatSaving.value) return
  batchCatSaving.value = true
  try {
    const res = await billApi.batchUpdateCategory([...selected.value], batchCatValue.value)
    await loadData()
    clearSelection()
    batchCatOpen.value = false
    toast.success(`已更新 ${res.updated_count} 条账单的分类`)
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '批量修改分类失败')
  } finally {
    batchCatSaving.value = false
  }
}
</script>

<template>
  <div class="page" style="--page-char: '记'">
    <PageHeader
      title="记账"
      sub="支出、收入、转账，笔笔有据；余额随记随清。"
      :dateline="`共 ${total} 条记录 · 按发生时间倒序`"
    >
      <button class="btn btn--primary" :disabled="!bookStore.currentBook" @click="openCreate">
        <SvgIcon name="plus" :size="16" />
        记一笔
      </button>
    </PageHeader>

    <EmptyState
      v-if="!bookStore.currentBook"
      icon="book"
      title="还没有账本"
      desc="记账需要先有一个账本，创建后就能开始记录。"
    >
      <template #action>
        <router-link to="/books" class="btn btn--primary">去创建账本</router-link>
      </template>
    </EmptyState>

    <template v-else>
      <div class="toolbar filter-bar card">
        <select v-model="filters.type" class="select filter-item" aria-label="类型筛选">
          <option value="">全部类型</option>
          <option v-for="t in BILL_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <select v-model="filters.category" class="select filter-item" aria-label="分类筛选">
          <option value="">全部分类</option>
          <optgroup v-if="expenseCats.length" label="支出">
            <option v-for="c in expenseCats" :key="c.id" :value="c.id">{{ c.name }}</option>
          </optgroup>
          <optgroup v-if="incomeCats.length" label="收入">
            <option v-for="c in incomeCats" :key="c.id" :value="c.id">{{ c.name }}</option>
          </optgroup>
        </select>
        <select v-model="filters.account" class="select filter-item" aria-label="账户筛选">
          <option value="">全部账户</option>
          <option v-for="a in optionAccounts" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
        <select v-model="filters.tag" class="select filter-item" aria-label="标签筛选">
          <option value="">全部标签</option>
          <option v-for="t in optionTags" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <input v-model="filters.start_date" type="date" class="input filter-item" aria-label="开始日期" />
        <span class="faint">至</span>
        <input v-model="filters.end_date" type="date" class="input filter-item" aria-label="结束日期" />
        <div class="keyword">
          <SvgIcon name="search" :size="16" style="color: var(--c-text-faint)" />
          <input v-model="filters.keyword" class="input keyword-input" placeholder="搜索备注" />
        </div>
        <button class="btn btn--ghost" @click="resetFilters">
          <SvgIcon name="refresh" :size="15" />
          重置
        </button>
      </div>

      <div v-if="selected.size > 0" class="batch-bar card">
        <span>已选 {{ selected.size }} 条</span>
        <button class="btn btn--ghost btn--sm" @click="openBatchCategory">
          <SvgIcon name="category" :size="15" />
          批量改分类
        </button>
        <button class="btn btn--danger-outline btn--sm" @click="batchDeleteConfirm = true">
          <SvgIcon name="trash" :size="15" />
          批量删除
        </button>
        <span class="spacer"></span>
        <button class="btn btn--ghost btn--sm" @click="clearSelection">取消选择</button>
      </div>

      <TableSkeleton v-if="loading" />

      <EmptyState
        v-else-if="total === 0"
        icon="bill"
        title="暂无符合条件的账单"
        desc="点右上角「记一笔」记录支出或收入；如有筛选条件，可尝试重置。"
      >
        <template #action>
          <button class="btn btn--primary" @click="openCreate">
            <SvgIcon name="plus" :size="16" />
            记一笔
          </button>
        </template>
      </EmptyState>

      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th class="th-index">No.</th>
                <th class="th-check">
                  <input
                    type="checkbox"
                    :checked="allChecked"
                    :indeterminate="someChecked && !allChecked"
                    aria-label="全选本页"
                    @change="togglePage"
                  />
                </th>
                <th>时间</th>
                <th>类型</th>
                <th>金额</th>
                <th>分类</th>
                <th>账户</th>
                <th>标签</th>
                <th>备注</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(b, i) in bills" :key="b.id">
                <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
                <td class="th-check">
                  <input
                    type="checkbox"
                    :checked="selected.has(b.id)"
                    aria-label="选择"
                    @change="toggleRow(b)"
                  />
                </td>
                <td class="muted">{{ fmtDateTime(b.occurred_at) }}</td>
                <td><span class="pill" :class="billTypePill(b.type)">{{ b.type_display }}</span></td>
                <td class="num">
                  <span :class="billAmountClass(b.type)">
                    {{ billSign(b.type) }}¥{{ money(b.amount) }}
                  </span>
                </td>
                <td>{{ b.category_name ?? '—' }}</td>
                <td class="muted">
                  {{ b.account_name }}<template v-if="b.type === 'transfer' && b.to_account_name"> → {{ b.to_account_name }}</template>
                </td>
                <td>
                  <div v-if="b.tag_names.length" class="tag-list">
                    <span v-for="(t, i) in b.tag_names.slice(0, 3)" :key="i" class="pill pill--neutral">{{ t }}</span>
                    <span v-if="b.tag_names.length > 3" class="faint">+{{ b.tag_names.length - 3 }}</span>
                  </div>
                  <span v-else class="faint">—</span>
                </td>
                <td class="muted" :title="b.remark">{{ b.remark || '—' }}</td>
                <td>
                  <div class="cell-actions">
                    <button class="btn btn--ghost btn--sm" @click="openEdit(b)">
                      <SvgIcon name="edit" :size="15" />
                      编辑
                    </button>
                    <button class="btn btn--danger-outline btn--sm" @click="deleting = b">
                      <SvgIcon name="trash" :size="15" />
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 移动端卡片列表（≤640px 时替换表格，避免横向滚动） -->
        <div class="bill-cards">
          <div v-for="b in bills" :key="b.id" class="bill-card">
            <label class="bill-card-check">
              <input
                type="checkbox"
                :checked="selected.has(b.id)"
                aria-label="选择账单"
                @change="toggleRow(b)"
              />
            </label>
            <div class="bill-card-main">
              <div class="bill-card-top">
                <span class="pill" :class="billTypePill(b.type)">{{ b.type_display }}</span>
                <span class="bill-card-amount num" :class="billAmountClass(b.type)">
                  {{ billSign(b.type) }}¥{{ money(b.amount) }}
                </span>
              </div>
              <div class="bill-card-meta">
                {{ fmtDateTime(b.occurred_at) }} · {{ b.category_name ?? '—' }}
                · {{ b.account_name
                }}<template v-if="b.type === 'transfer' && b.to_account_name"> → {{ b.to_account_name }}</template>
              </div>
              <div v-if="b.tag_names.length || b.remark" class="bill-card-foot">
                <span v-for="(t, i) in b.tag_names.slice(0, 3)" :key="i" class="pill pill--neutral">{{ t }}</span>
                <span v-if="b.remark" class="bill-card-remark" :title="b.remark">{{ b.remark }}</span>
              </div>
            </div>
            <div class="bill-card-actions">
              <button class="btn btn--ghost btn--sm" aria-label="编辑" @click="openEdit(b)">
                <SvgIcon name="edit" :size="15" />
                编辑
              </button>
              <button class="btn btn--danger-outline btn--sm" aria-label="删除" @click="deleting = b">
                <SvgIcon name="trash" :size="15" />
                删除
              </button>
            </div>
          </div>
        </div>
        <PaginationBar
          :page="page"
          :size="size"
          :total="total"
          :pages="pages"
          @update:page="onPageChange"
          @update:size="onSizeChange"
        />
      </template>
    </template>

    <BillFormModal
      v-if="modalOpen"
      :is-edit="isEdit"
      :book-id="bookStore.currentBook?.id ?? 0"
      :bill="editingBill"
      :categories="optionCategories"
      :accounts="optionAccounts"
      :tags="optionTags"
      @close="modalOpen = false"
      @saved="onSaved"
    />

    <ConfirmDialog
      v-if="deleting"
      title="删除账单"
      :message="`确定删除这条${deleting.type_display}（¥${money(deleting.amount)}）吗？账单将移入回收站，对应账户余额会回滚。`"
      confirm-text="删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />

    <ConfirmDialog
      v-if="batchDeleteConfirm"
      title="批量删除"
      :message="`将删除选中的 ${selected.size} 条账单并移入回收站，账户余额同步回滚。是否继续？`"
      confirm-text="删除"
      :loading="batchDeleting"
      @cancel="batchDeleteConfirm = false"
      @confirm="confirmBatchDelete"
    />

    <BaseModal v-if="batchCatOpen" small as-form title="批量修改分类" @close="batchCatOpen = false" @submit="confirmBatchCategory">
      <div class="field">
        <label class="field-label">选择新分类<span class="field-hint">（共 {{ selected.size }} 条账单）</span></label>
        <select v-model="batchCatValue" class="select">
          <option value="" disabled>请选择分类</option>
          <optgroup v-if="batchCatOptions.expense.length" label="支出">
            <option v-for="c in batchCatOptions.expense" :key="c.id" :value="c.id">{{ c.name }}</option>
          </optgroup>
          <optgroup v-if="batchCatOptions.income.length" label="收入">
            <option v-for="c in batchCatOptions.income" :key="c.id" :value="c.id">{{ c.name }}</option>
          </optgroup>
        </select>
        <p v-if="selectedTypeLabel" class="field-hint" style="margin-top: 6px">
          {{ selectedTypeLabel === '混合类型' ? '所选账单类型不一致，请按账单类型选择对应分类。' : `所选账单均为${selectedTypeLabel}，只显示${selectedTypeLabel}分类。` }}
        </p>
      </div>
      <template #footer>
        <button class="btn" type="button" :disabled="batchCatSaving" @click="batchCatOpen = false">取消</button>
        <button
          class="btn btn--primary"
          type="submit"
          :disabled="batchCatSaving || batchCatValue === ''"
          @click="confirmBatchCategory"
        >
          {{ batchCatSaving ? '保存中…' : '确定' }}
        </button>
      </template>
    </BaseModal>
    <p class="page-aphorism">一粥一饭，当思来处不易。</p>
  </div>
</template>

<style scoped>
.filter-bar {
  padding: 12px;
  flex-wrap: nowrap;
  align-items: center;
  overflow-x: auto;
}

.filter-item {
  flex: 1 1 140px;
  min-width: 130px;
  max-width: 190px;
}

.keyword {
  position: relative;
  flex: 1 1 180px;
  min-width: 150px;
}

.keyword svg {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.keyword-input {
  padding-left: 36px;
}

.th-check {
  width: 44px;
}

.th-check input {
  width: 18px;
  height: 18px;
  accent-color: var(--c-primary);
}

.tag-list {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
  font-size: 14px;
  box-shadow: 0 0 0 2px var(--c-primary-bg);
  border-color: var(--c-primary-bg);
}

.batch-bar > span:first-child {
  font-weight: 600;
  color: var(--c-primary);
}

/* ---------- 移动端卡片列表（默认隐藏，≤640px 替换表格） ---------- */
.bill-cards {
  display: none;
}

@media (max-width: 640px) {
  .table-wrap {
    display: none;
  }

  .bill-cards {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .bill-card {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 12px 14px;
    border: 1px solid var(--c-border);
    border-radius: var(--radius);
    background: var(--c-surface);
    box-shadow: var(--shadow-soft);
  }

  .bill-card-check {
    margin-top: 3px;
    flex: none;
  }

  .bill-card-check input {
    width: 18px;
    height: 18px;
    accent-color: var(--c-primary);
  }

  .bill-card-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .bill-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .bill-card-amount {
    font-weight: 600;
    font-size: 15px;
  }

  .bill-card-meta {
    font-size: 13px;
    color: var(--c-text-secondary);
    line-height: 1.5;
  }

  .bill-card-foot {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }

  .bill-card-remark {
    font-size: 12.5px;
    color: var(--c-text-secondary);
    margin: 0;
  }

  .bill-card-actions {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: none;
  }
}
</style>
