<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { tagApi } from '@/api/tag'
import { ApiError } from '@/api/http'
import { fmtDate } from '@/utils/format'
import { CATEGORY_COLORS } from '@/utils/constants'
import type { Tag } from '@/types/api'
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

const tags = ref<Tag[]>([])
const loading = ref(false)
const { page, size, total, pages, paged, go } = usePagination(tags, 10)

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
    const list = await tagApi.list({ book: bookId })
    if (my !== loadSeq) return
    tags.value = list
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '标签加载失败')
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

const form = reactive<{ id: number | null; name: string; color: string }>({
  id: null,
  name: '',
  color: CATEGORY_COLORS[1]!,
})

const formErrors = reactive<Record<string, string>>({})

function openCreate(): void {
  isEdit.value = false
  Object.assign(form, { id: null, name: '', color: CATEGORY_COLORS[1]! })
  formErrors.name = ''
  modalOpen.value = true
}

function openEdit(row: Tag): void {
  isEdit.value = true
  Object.assign(form, { id: row.id, name: row.name, color: row.color || CATEGORY_COLORS[1]! })
  formErrors.name = ''
  modalOpen.value = true
}

function validateForm(): boolean {
  formErrors.name = form.name.trim() ? '' : '请输入标签名称'
  if (!formErrors.name && form.name.trim().length > 50) formErrors.name = '名称不能超过 50 字'
  return !formErrors.name
}

async function onSubmit(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId || !validateForm() || saving.value) return
  saving.value = true
  try {
    const payload = { book: bookId, name: form.name.trim(), color: form.color }
    if (isEdit.value && form.id !== null) await tagApi.update(form.id, payload)
    else await tagApi.create(payload)
    modalOpen.value = false
    await loadData()
    toast.success(isEdit.value ? '标签已更新' : '标签已创建')
  } catch (e) {
    if (e instanceof ApiError && e.status === 400) toast.error(e.message)
    else toast.error(e instanceof ApiError ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/* ---------- 删除 ---------- */
const deleting = ref<Tag | null>(null)
const deleteLoading = ref(false)

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await tagApi.remove(deleting.value.id)
    tags.value = tags.value.filter((t) => t.id !== deleting.value!.id)
    toast.success('标签已删除')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <div class="page" style="--page-char: '签'">
    <PageHeader
      title="标签"
      sub="事以签记，按签归类；统计筛选，一索即得。"
      :dateline="`共 ${tags.length} 个标签 · 同一账本内名称唯一`"
    >
      <button class="btn btn--primary" :disabled="!bookStore.currentBook" @click="openCreate">
        <SvgIcon name="plus" :size="16" />
        新建标签
      </button>
    </PageHeader>

    <EmptyState
      v-if="!bookStore.currentBook"
      icon="book"
      title="还没有账本"
      desc="标签归属于账本，请先创建或切换账本。"
    >
      <template #action>
        <router-link to="/books" class="btn btn--primary">去创建账本</router-link>
      </template>
    </EmptyState>

    <TableSkeleton v-else-if="loading" />

    <EmptyState
      v-else-if="tags.length === 0"
      icon="tag"
      title="还没有标签"
      desc="先建一个标签，记账时就能给账单打上标签。"
    >
      <template #action>
        <button class="btn btn--primary" @click="openCreate">
          <SvgIcon name="plus" :size="16" />
          新建标签
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
              <th>颜色</th>
              <th>账单数</th>
              <th>创建时间</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in paged" :key="row.id">
              <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
              <td>
                <div class="tag-name">
                  <span class="dot" :style="{ background: row.color || 'var(--c-border-strong)' }"></span>
                  <span>{{ row.name }}</span>
                </div>
              </td>
              <td><span class="mono faint">{{ row.color || '—' }}</span></td>
              <td class="num">{{ row.bill_count }}</td>
              <td class="muted">{{ fmtDate(row.created_at) }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn--ghost btn--sm" @click="openEdit(row)">
                    <SvgIcon name="edit" :size="15" />
                    编辑
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

    <BaseModal v-if="modalOpen" :title="isEdit ? '编辑标签' : '新建标签'" small @close="modalOpen = false">
      <FormField label="标签名称（必填，≤50 字，同一账本内唯一）" :error="formErrors.name">
        <input
          v-model="form.name"
          class="input"
          :class="{ 'input--invalid': formErrors.name }"
          maxlength="50"
          placeholder="如：聚餐"
        />
      </FormField>
      <FormField label="颜色" class="field-gap">
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
      <template #footer>
        <button class="btn" :disabled="saving" @click="modalOpen = false">取消</button>
        <button class="btn btn--primary" :disabled="saving" @click="onSubmit">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </BaseModal>

    <ConfirmDialog
      v-if="deleting"
      title="删除标签"
      :message="`删除标签「${deleting.name}」后，账单上的该标签会被移除。确定删除吗？`"
      confirm-text="删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
    <p class="page-aphorism">积微成著，日积月累。</p>
  </div>
</template>

<style scoped>
.field-gap {
  margin-top: 16px;
}

.tag-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}
</style>
