<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { categoryApi } from '@/api/category'
import { ApiError } from '@/api/http'
import { fmtDate, money, toNumber } from '@/utils/format'
import { CATEGORY_COLORS, CATEGORY_TYPES, DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES } from '@/utils/constants'
import type { Category, CategoryType } from '@/types/api'
import SvgIcon from '@/components/SvgIcon.vue'
import PageHeader from '@/components/PageHeader.vue'
import TableSkeleton from '@/components/TableSkeleton.vue'
import FormField from '@/components/FormField.vue'
import BaseModal from '@/components/BaseModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const bookStore = useBookStore()
const toast = useToast()

const typeTab = ref<CategoryType>('expense')
const categories = ref<Category[]>([])
const loading = ref(false)
const creatingDefaults = ref(false)

const filtered = computed(() => categories.value.filter((c) => c.type === typeTab.value))
const { page, size, total, pages, paged, go } = usePagination(filtered, 10)

function onSizeChange(v: number): void {
  size.value = v
}

let loadSeq = 0

async function loadData(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId) return
  const my = ++loadSeq
  loading.value = true
  try {
    const list = await categoryApi.list({ book: bookId })
    if (my !== loadSeq) return
    categories.value = list
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '分类加载失败')
  } finally {
    if (my === loadSeq) loading.value = false
  }
}

watch(
  () => bookStore.currentBook?.id,
  () => void loadData(),
  { immediate: true },
)

/* ---------- 新增 / 编辑 ---------- */
const modalOpen = ref(false)
const isEdit = ref(false)
const saving = ref(false)

const form = reactive<{
  id: number | null
  name: string
  type: CategoryType
  color: string
  budget: string
}>({ id: null, name: '', type: 'expense', color: CATEGORY_COLORS[0]!, budget: '' })

const formErrors = reactive<Record<string, string>>({})

function openCreate(): void {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    type: typeTab.value,
    color: CATEGORY_COLORS[0]!,
    budget: '',
  })
  formErrors.name = ''
  formErrors.budget = ''
  modalOpen.value = true
}

function openEdit(row: Category): void {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    type: row.type,
    color: row.color || CATEGORY_COLORS[0]!,
    budget: String(toNumber(row.budget)),
  })
  formErrors.name = ''
  formErrors.budget = ''
  modalOpen.value = true
}

function validateForm(): boolean {
  formErrors.name = form.name.trim() ? '' : '请输入分类名称'
  if (!formErrors.name && form.name.trim().length > 100) formErrors.name = '名称不能超过 100 字'
  const budget = Number(form.budget)
  if (form.budget !== '' && (Number.isNaN(budget) || budget < 0)) formErrors.budget = '预算需为不小于 0 的数字'
  else formErrors.budget = ''
  return !formErrors.name && !formErrors.budget
}

async function onSubmit(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId || !validateForm() || saving.value) return
  saving.value = true
  try {
    const payload = {
      book: bookId,
      name: form.name.trim(),
      type: form.type,
      color: form.color,
      icon: '',
      budget: toNumber(form.budget),
    }
    if (isEdit.value && form.id !== null) await categoryApi.update(form.id, payload)
    else await categoryApi.create(payload)
    modalOpen.value = false
    await loadData()
    toast.success(isEdit.value ? '分类已更新' : '分类已创建')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/* ---------- 启用 / 停用 / 删除 ---------- */
const busyId = ref<number | null>(null)

async function toggleActive(row: Category): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = row.id
  try {
    const result = row.is_active ? await categoryApi.disable(row.id) : await categoryApi.enable(row.id)
    const idx = categories.value.findIndex((c) => c.id === result.id)
    if (idx >= 0) categories.value[idx] = result
    toast.success(row.is_active ? '分类已禁用' : '分类已启用')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '操作失败')
  } finally {
    busyId.value = null
  }
}

const deleting = ref<Category | null>(null)
const deleteLoading = ref(false)

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await categoryApi.remove(deleting.value.id)
    categories.value = categories.value.filter((c) => c.id !== deleting.value!.id)
    toast.success('分类已删除')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

/* ---------- 一键生成默认分类 ---------- */
async function createDefaults(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId || creatingDefaults.value) return
  creatingDefaults.value = true
  const defaults = typeTab.value === 'expense' ? DEFAULT_EXPENSE_CATEGORIES : DEFAULT_INCOME_CATEGORIES
  const existing = new Set(categories.value.filter((c) => c.type === typeTab.value).map((c) => c.name))
  const missing = defaults.filter((n) => !existing.has(n))
  try {
    for (const [i, name] of missing.entries()) {
      await categoryApi.create({
        book: bookId,
        name,
        type: typeTab.value,
        color: CATEGORY_COLORS[i % CATEGORY_COLORS.length]!,
        icon: '',
        budget: 0,
      })
    }
    await loadData()
    if (missing.length > 0) toast.success(`已生成 ${missing.length} 个默认${typeTab.value === 'expense' ? '支出' : '收入'}分类`)
    else toast.info('默认分类已存在，无需重复生成')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '生成失败')
  } finally {
    creatingDefaults.value = false
  }
}
</script>

<template>
  <div class="page" style="--page-char: '类'">
    <PageHeader
      title="分类"
      sub="收入支出，各归其类；可设预算，量入为出。"
      :dateline="`${typeTab === 'expense' ? '支出' : '收入'}分类 ${filtered.length} 个 · 可为分类设定月度预算`"
    >
      <button class="btn" :disabled="!bookStore.currentBook || creatingDefaults" @click="createDefaults">
        {{ creatingDefaults ? '生成中…' : '生成默认分类' }}
      </button>
      <button class="btn btn--primary" :disabled="!bookStore.currentBook" @click="openCreate">
        <SvgIcon name="plus" :size="16" />
        新建分类
      </button>
    </PageHeader>

    <EmptyState
      v-if="!bookStore.currentBook"
      icon="book"
      title="还没有账本"
      desc="分类归属于账本，请先创建或切换账本。"
    >
      <template #action>
        <router-link to="/books" class="btn btn--primary">去创建账本</router-link>
      </template>
    </EmptyState>

    <template v-else>
      <div class="toolbar toolbar--between">
        <div class="segmented" role="tablist" aria-label="分类类型">
          <button
            v-for="t in CATEGORY_TYPES"
            :key="t.value"
            class="segmented-item"
            :class="{ 'is-active': typeTab === t.value }"
            @click="typeTab = t.value"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <TableSkeleton v-if="loading" />

      <EmptyState
        v-else-if="filtered.length === 0"
        icon="category"
        :title="`还没有${typeTab === 'expense' ? '支出' : '收入'}分类`"
        desc="可以手动新建，也可以一键生成常用默认分类。"
      >
        <template #action>
          <button class="btn" :disabled="creatingDefaults" @click="createDefaults">
            {{ creatingDefaults ? '生成中…' : '生成默认分类' }}
          </button>
        </template>
      </EmptyState>

      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th class="th-index">No.</th>
                <th>名称</th>
                <th>类型</th>
                <th>预算</th>
                <th>状态</th>
                <th>创建时间</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in paged" :key="row.id">
                <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
                <td>
                  <div class="cat-name">
                    <span class="dot" :style="{ background: row.color || 'var(--c-border-strong)' }"></span>
                    <span>{{ row.name }}</span>
                    <span v-if="row.is_default" class="pill pill--neutral">默认</span>
                  </div>
                </td>
                <td><span class="pill" :class="row.type === 'expense' ? 'pill--danger' : 'pill--success'">{{ row.type_display }}</span></td>
                <td class="num">¥{{ money(row.budget) }}</td>
                <td>
                  <span class="pill" :class="row.is_active ? 'pill--success' : 'pill--neutral'">
                    {{ row.is_active ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="muted">{{ fmtDate(row.created_at) }}</td>
                <td>
                  <div class="cell-actions">
                    <button class="btn btn--ghost btn--sm" :disabled="busyId !== null" @click="openEdit(row)">
                      <SvgIcon name="edit" :size="15" />
                      编辑
                    </button>
                    <button
                      class="btn btn--ghost btn--sm"
                      :disabled="busyId !== null"
                      @click="toggleActive(row)"
                    >
                      <SvgIcon :name="row.is_active ? 'archive' : 'restore'" :size="15" />
                      {{ row.is_active ? '禁用' : '启用' }}
                    </button>
                    <button class="btn btn--danger-outline btn--sm" @click="deleting = row">
                      <SvgIcon name="trash" :size="15" />
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar
          :page="page"
          :size="size"
          :total="total"
          :pages="pages"
          @update:page="go"
          @update:size="onSizeChange"
        />
      </template>
    </template>

    <BaseModal v-if="modalOpen" :title="isEdit ? '编辑分类' : '新建分类'" @close="modalOpen = false">
      <div class="form-grid">
        <FormField label="分类名称（必填，≤100 字）" :error="formErrors.name" :span="2">
          <input
            v-model="form.name"
            class="input"
            :class="{ 'input--invalid': formErrors.name }"
            maxlength="100"
            :placeholder="typeTab === 'expense' ? '如：餐饮' : '如：工资'"
          />
        </FormField>

        <FormField label="类型" :span="2">
          <div class="segmented form-type">
            <button
              v-for="t in CATEGORY_TYPES"
              :key="t.value"
              type="button"
              class="segmented-item"
              :class="{ 'is-active': form.type === t.value }"
              :disabled="isEdit"
              @click="form.type = t.value"
            >
              {{ t.label }}
            </button>
          </div>
        </FormField>

        <FormField label="颜色" :span="2">
          <div class="color-palette">
            <button
              v-for="c in CATEGORY_COLORS"
              :key="c"
              type="button"
              class="color-swatch"
              :class="{ 'is-selected': form.color === c }"
              :style="{ background: c }"
              :aria-label="`选择颜色 ${c}`"
              @click="form.color = c"
            ></button>
          </div>
        </FormField>

        <FormField label="分类月度预算" :error="formErrors.budget" :span="2">
          <input
            v-model="form.budget"
            type="number"
            min="0"
            step="0.01"
            class="input"
            :class="{ 'input--invalid': formErrors.budget }"
            placeholder="0.00，0 表示不设预算"
          />
        </FormField>
      </div>
      <template #footer>
        <button class="btn" :disabled="saving" @click="modalOpen = false">取消</button>
        <button class="btn btn--primary" :disabled="saving" @click="onSubmit">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </BaseModal>

    <ConfirmDialog
      v-if="deleting"
      title="删除分类"
      :message="`删除分类「${deleting.name}」后，该分类下的账单会变成未分类。确定删除吗？`"
      confirm-text="删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
    <p class="page-aphorism">物以类聚，人以群分。</p>
  </div>
</template>

<style scoped>
.cat-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.form-type .segmented-item {
  flex: 1;
  min-height: 44px;
  justify-content: center;
}

.segmented-item:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
