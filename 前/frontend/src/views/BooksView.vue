<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { bookApi } from '@/api/book'
import { ApiError } from '@/api/http'
import { fmtDate, money, toNumber } from '@/utils/format'
import type { Book } from '@/types/api'
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

type ArchiveFilter = 'all' | 'active' | 'archived'
const archiveFilter = ref<ArchiveFilter>('all')

const loading = ref(false)
const filtered = computed(() => {
  const list = bookStore.books
  if (archiveFilter.value === 'active') return list.filter((b) => !b.is_archived)
  if (archiveFilter.value === 'archived') return list.filter((b) => b.is_archived)
  return list
})
const { page, size, total, pages, paged, go } = usePagination(filtered, 10)

function onSizeChange(v: number): void {
  size.value = v
}

/* ---------- 新增 / 编辑弹窗 ---------- */
const modalOpen = ref(false)
const isEdit = ref(false)
const form = reactive<{ id: number | null; name: string; remark: string; budget: string; cover: string; is_default: boolean }>({
  id: null,
  name: '',
  remark: '',
  budget: '',
  cover: '',
  is_default: false,
})
const fieldErrors = reactive<Record<string, string>>({})
const saving = ref(false)

function openCreate(): void {
  isEdit.value = false
  Object.assign(form, { id: null, name: '', remark: '', budget: '', cover: '', is_default: false })
  fieldErrors.name = ''
  fieldErrors.budget = ''
  modalOpen.value = true
}

function openEdit(row: Book): void {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    remark: row.remark,
    budget: String(toNumber(row.budget)),
    cover: row.cover,
    is_default: row.is_default,
  })
  fieldErrors.name = ''
  fieldErrors.budget = ''
  modalOpen.value = true
}

function validateForm(): boolean {
  fieldErrors.name = form.name.trim() ? '' : '请输入账本名称'
  if (!fieldErrors.name && form.name.trim().length > 100) fieldErrors.name = '名称不能超过 100 字'
  const budget = Number(form.budget)
  if (form.budget !== '' && (Number.isNaN(budget) || budget < 0)) fieldErrors.budget = '预算需为不小于 0 的数字'
  else fieldErrors.budget = ''
  if (form.cover.trim().length > 200) fieldErrors.cover = '封面地址不能超过 200 字'
  return !fieldErrors.name && !fieldErrors.budget && !fieldErrors.cover
}

async function onSubmit(): Promise<void> {
  if (!validateForm() || saving.value) return
  saving.value = true
  try {
    let result: Book
    const payload = {
      name: form.name.trim(),
      remark: form.remark.trim(),
      budget: toNumber(form.budget),
      cover: form.cover.trim(),
    }
    if (isEdit.value && form.id !== null) {
      result = await bookApi.update(form.id, payload)
    } else {
      result = await bookApi.create(payload)
    }
    if (form.is_default) result = await bookApi.setDefault(result.id)
    bookStore.sync(result)
    if (!bookStore.currentBookId) bookStore.setCurrentBook(result.id)
    modalOpen.value = false
    toast.success(isEdit.value ? '账本已更新' : '账本已创建')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/* ---------- 归档 / 设为默认 / 删除 ---------- */
const busyId = ref<number | null>(null)

async function toggleArchive(row: Book): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = row.id
  try {
    const result = row.is_archived ? await bookApi.unarchive(row.id) : await bookApi.archive(row.id)
    bookStore.sync(result)
    toast.success(row.is_archived ? '已取消归档' : '已归档')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '操作失败')
  } finally {
    busyId.value = null
  }
}

async function makeDefault(row: Book): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = row.id
  try {
    const result = await bookApi.setDefault(row.id)
    bookStore.sync(result)
    toast.success(`已将「${result.name}」设为默认账本`)
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '操作失败')
  } finally {
    busyId.value = null
  }
}

const deleting = ref<Book | null>(null)
const deleteLoading = ref(false)

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await bookApi.remove(deleting.value.id)
    bookStore.remove(deleting.value.id)
    toast.success('账本已删除')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(async () => {
  try {
    loading.value = true
    await bookStore.fetchBooks()
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '账本加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page" style="--page-char: '账'">
    <PageHeader
      title="账本"
      sub="各账各本，互不相扰；月度预算，删时三思。"
      :dateline="`共 ${bookStore.books.length} 个账本 · 默认账本在记账时优先使用`"
    >
      <button class="btn btn--primary" @click="openCreate">
        <SvgIcon name="plus" :size="16" />
        新建账本
      </button>
    </PageHeader>

    <div class="toolbar toolbar--between">
      <div class="segmented" role="tablist" aria-label="归档筛选">
        <button
          v-for="(f, key) in { all: '全部', active: '未归档', archived: '已归档' } as Record<ArchiveFilter, string>"
          :key="key"
          class="segmented-item"
          :class="{ 'is-active': archiveFilter === key }"
          @click="archiveFilter = key"
        >
          {{ f }}
        </button>
      </div>
    </div>

    <TableSkeleton v-if="loading" />

    <EmptyState
      v-else-if="bookStore.books.length === 0"
      icon="book"
      title="还没有账本"
      desc="先建一个账本，再往里记支出和收入。"
    >
      <template #action>
        <button class="btn btn--primary" @click="openCreate">
          <SvgIcon name="plus" :size="16" />
          新建账本
        </button>
      </template>
    </EmptyState>

    <EmptyState
      v-else-if="filtered.length === 0"
      icon="filter"
      title="这个分类下没有账本"
      desc="试试切换到全部账本查看。"
    />

    <template v-else>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th class="th-index">No.</th>
              <th>名称</th>
              <th>月度预算</th>
              <th>账单</th>
              <th>账户</th>
              <th>备注</th>
              <th>创建时间</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in paged" :key="row.id">
              <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
              <td>
                <div class="book-name">
                  <span>{{ row.name }}</span>
                  <span v-if="row.is_default" class="pill pill--primary">默认</span>
                  <span v-if="row.is_archived" class="pill pill--neutral">已归档</span>
                </div>
              </td>
              <td class="num">¥{{ money(row.budget) }}</td>
              <td class="num">{{ row.bill_count }}</td>
              <td class="num">{{ row.account_count }}</td>
              <td class="muted" :title="row.remark">{{ row.remark || '—' }}</td>
              <td class="muted">{{ fmtDate(row.created_at) }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn--ghost btn--sm" :disabled="busyId !== null" @click="openEdit(row)">
                    <SvgIcon name="edit" :size="15" />
                    编辑
                  </button>
                  <button
                    v-if="!row.is_default"
                    class="btn btn--ghost btn--sm"
                    :disabled="busyId !== null"
                    @click="makeDefault(row)"
                  >
                    <SvgIcon name="star" :size="15" />
                    设默认
                  </button>
                  <button
                    class="btn btn--ghost btn--sm"
                    :disabled="busyId !== null"
                    @click="toggleArchive(row)"
                  >
                    <SvgIcon :name="row.is_archived ? 'restore' : 'archive'" :size="15" />
                    {{ row.is_archived ? '取消归档' : '归档' }}
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

    <BaseModal
      v-if="modalOpen"
      :title="isEdit ? '编辑账本' : '新建账本'"
      @close="modalOpen = false"
    >
      <div class="form-grid">
        <FormField label="账本名称（必填，≤100 字）" :error="fieldErrors.name" :span="2">
          <input
            v-model="form.name"
            class="input"
            :class="{ 'input--invalid': fieldErrors.name }"
            maxlength="100"
            placeholder="如：日常账本"
          />
        </FormField>

        <FormField label="月度预算" :error="fieldErrors.budget" :span="2">
          <input
            v-model="form.budget"
            type="number"
            min="0"
            step="0.01"
            class="input"
            :class="{ 'input--invalid': fieldErrors.budget }"
            placeholder="0.00"
          />
        </FormField>

        <FormField label="封面地址" :error="fieldErrors.cover" :span="2">
          <input
            v-model="form.cover"
            class="input"
            maxlength="200"
            placeholder="可选，图片链接"
          />
        </FormField>

        <FormField label="备注" :span="2">
          <textarea v-model="form.remark" class="textarea" maxlength="500" placeholder="可选"></textarea>
        </FormField>

        <label class="check-row" style="grid-column: span 2">
          <input v-model="form.is_default" type="checkbox" />
          <span>设为默认账本</span>
        </label>
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
      title="删除账本"
      :message="`删除账本「${deleting.name}」会一并删除其下所有账户、分类、标签和账单，无法恢复。确定要删除吗？`"
      confirm-text="删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
    <p class="page-aphorism">日清月结，心中有数。</p>
  </div>
</template>

<style scoped>
.book-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  font-size: 14px;
  cursor: pointer;
}

.check-row input {
  width: 16px;
  height: 16px;
  accent-color: var(--c-primary);
}
</style>
