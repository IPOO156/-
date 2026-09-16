<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { accountApi } from '@/api/account'
import { ApiError } from '@/api/http'
import { fmtDate, money, toNumber } from '@/utils/format'
import { ACCOUNT_TYPES } from '@/utils/constants'
import type { Account, AccountType } from '@/types/api'
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

type ActiveFilter = 'all' | 'active' | 'disabled'
const activeFilter = ref<ActiveFilter>('all')

const accounts = ref<Account[]>([])
const loading = ref(false)

const filtered = computed(() => {
  if (activeFilter.value === 'active') return accounts.value.filter((a) => a.is_active)
  if (activeFilter.value === 'disabled') return accounts.value.filter((a) => !a.is_active)
  return accounts.value
})

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
    const list = await accountApi.list({ book: bookId })
    if (my !== loadSeq) return
    accounts.value = list
  } catch (e) {
    if (my === loadSeq) toast.error(e instanceof ApiError ? e.message : '账户加载失败')
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
  type: AccountType
  initial_balance: string
}>({ id: null, name: '', type: 'cash', initial_balance: '' })

const formErrors = reactive<Record<string, string>>({})

function openCreate(): void {
  isEdit.value = false
  Object.assign(form, { id: null, name: '', type: 'cash', initial_balance: '' })
  formErrors.name = ''
  formErrors.initial_balance = ''
  modalOpen.value = true
}

function openEdit(row: Account): void {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    type: row.type,
    initial_balance: String(toNumber(row.initial_balance)),
  })
  formErrors.name = ''
  formErrors.initial_balance = ''
  modalOpen.value = true
}

function validateForm(): boolean {
  formErrors.name = form.name.trim() ? '' : '请输入账户名称'
  if (!formErrors.name && form.name.trim().length > 100) formErrors.name = '名称不能超过 100 字'
  const bal = Number(form.initial_balance)
  if (form.initial_balance !== '' && (Number.isNaN(bal) || bal < 0))
    formErrors.initial_balance = '初始余额需为不小于 0 的数字'
  else formErrors.initial_balance = ''
  return !formErrors.name && !formErrors.initial_balance
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
      initial_balance: toNumber(form.initial_balance),
    }
    if (isEdit.value && form.id !== null) await accountApi.update(form.id, payload)
    else await accountApi.create(payload)
    modalOpen.value = false
    await loadData()
    toast.success(isEdit.value ? '账户已更新' : '账户已创建')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/* ---------- 启用 / 停用 / 删除 ---------- */
const busyId = ref<number | null>(null)

async function toggleActive(row: Account): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = row.id
  try {
    const result = row.is_active ? await accountApi.disable(row.id) : await accountApi.enable(row.id)
    const idx = accounts.value.findIndex((a) => a.id === result.id)
    if (idx >= 0) accounts.value[idx] = result
    toast.success(row.is_active ? '账户已停用' : '账户已启用')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '操作失败')
  } finally {
    busyId.value = null
  }
}

const deleting = ref<Account | null>(null)
const deleteLoading = ref(false)

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await accountApi.remove(deleting.value.id)
    accounts.value = accounts.value.filter((a) => a.id !== deleting.value!.id)
    toast.success('账户已删除')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

/* ---------- 账户互转 ---------- */
const transferOpen = ref(false)
const transferSaving = ref(false)
const transferForm = reactive<{ from: number | null; to: number | null; amount: string; remark: string }>({
  from: null,
  to: null,
  amount: '',
  remark: '',
})
const transferErrors = reactive<Record<string, string>>({})

const transferableOptions = computed(() =>
  accounts.value.filter((a) => a.id !== transferForm.from && a.is_active),
)

function openTransfer(): void {
  Object.assign(transferForm, { from: null, to: null, amount: '', remark: '' })
  transferErrors.from = ''
  transferErrors.to = ''
  transferErrors.amount = ''
  transferOpen.value = true
}

async function submitTransfer(): Promise<void> {
  transferErrors.from = transferForm.from === null ? '请选择转出账户' : ''
  transferErrors.amount = transferForm.amount === '' || Number(transferForm.amount) <= 0 ? '请输入大于 0 的金额' : ''
  transferErrors.to =
    transferForm.to === null ? '请选择转入账户' : transferForm.to === transferForm.from ? '转入账户不能与转出账户相同' : ''
  if (Object.values(transferErrors).some(Boolean) || transferSaving.value) return

  transferSaving.value = true
  try {
    await accountApi.transfer({
      from_account: transferForm.from as number,
      to_account: transferForm.to as number,
      amount: Number(transferForm.amount),
      remark: transferForm.remark.trim() || '账户转账',
    })
    transferOpen.value = false
    await loadData()
    toast.success('转账完成，双方余额已更新')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '转账失败')
  } finally {
    transferSaving.value = false
  }
}
</script>

<template>
  <div class="page" style="--page-char: '财'">
    <PageHeader
      title="账户"
      sub="现金、微信、支付宝、银行卡，各归其位；余额随流水而增减。"
      :dateline="`共 ${accounts.length} 个账户 · 当前余额随账单实时变动`"
    >
      <button class="btn" :disabled="!bookStore.currentBook" @click="openTransfer">
        <SvgIcon name="transfer" :size="16" />
        账户互转
      </button>
      <button class="btn btn--primary" :disabled="!bookStore.currentBook" @click="openCreate">
        <SvgIcon name="plus" :size="16" />
        新建账户
      </button>
    </PageHeader>

    <EmptyState
      v-if="!bookStore.currentBook"
      icon="book"
      title="还没有账本"
      desc="账户归属于账本，请先创建或切换账本。"
    >
      <template #action>
        <router-link to="/books" class="btn btn--primary">去创建账本</router-link>
      </template>
    </EmptyState>

    <template v-else>
      <div class="toolbar toolbar--between">
        <div class="segmented" role="tablist" aria-label="状态筛选">
          <button
            v-for="(f, key) in { all: '全部', active: '启用', disabled: '停用' } as Record<ActiveFilter, string>"
            :key="key"
            class="segmented-item"
            :class="{ 'is-active': activeFilter === key }"
            @click="activeFilter = key"
          >
            {{ f }}
          </button>
        </div>
      </div>

      <TableSkeleton v-if="loading" />

      <EmptyState
        v-else-if="accounts.length === 0"
        icon="wallet"
        title="还没有账户"
        desc="先建一个账户（如微信钱包、现金），记账时才能选择从哪个账户出账。"
      >
        <template #action>
          <button class="btn btn--primary" @click="openCreate">
            <SvgIcon name="plus" :size="16" />
            新建账户
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
                <th>初始余额</th>
                <th>当前余额</th>
                <th>状态</th>
                <th>创建时间</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in paged" :key="row.id">
                <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
                <td style="font-weight: 500">{{ row.name }}</td>
                <td><span class="pill pill--neutral">{{ row.type_display }}</span></td>
                <td class="num muted">¥{{ money(row.initial_balance) }}</td>
                <td class="num"><span :class="toNumber(row.balance) >= 0 ? 'money-in' : 'money-out'">¥{{ money(row.balance) }}</span></td>
                <td>
                  <span class="pill" :class="row.is_active ? 'pill--success' : 'pill--neutral'">
                    {{ row.is_active ? '启用' : '停用' }}
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
                      {{ row.is_active ? '停用' : '启用' }}
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

    <BaseModal v-if="modalOpen" :title="isEdit ? '编辑账户' : '新建账户'" @close="modalOpen = false">
      <div class="form-grid">
        <FormField label="账户名称（必填，≤100 字）" :error="formErrors.name" :span="2">
          <input
            v-model="form.name"
            class="input"
            :class="{ 'input--invalid': formErrors.name }"
            maxlength="100"
            placeholder="如：微信钱包"
          />
        </FormField>

        <FormField label="账户类型" :span="2">
          <select v-model="form.type" class="select">
            <option v-for="t in ACCOUNT_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </FormField>

        <FormField label="初始余额" :error="formErrors.initial_balance" :hint="isEdit ? '初始余额不可修改，当前余额随账单自动变化。' : undefined" :span="2">
          <input
            v-model="form.initial_balance"
            type="number"
            min="0"
            step="0.01"
            class="input"
            :disabled="isEdit"
            :class="{ 'input--invalid': formErrors.initial_balance }"
            placeholder="0.00"
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

    <BaseModal v-if="transferOpen" title="账户互转" @close="transferOpen = false">
      <div class="form-grid">
        <FormField label="转出账户" :error="transferErrors.from" :span="2">
          <select v-model="transferForm.from" class="select" :class="{ 'input--invalid': transferErrors.from }">
            <option :value="null" disabled>请选择转出账户</option>
            <option v-for="a in accounts.filter((x) => x.is_active)" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </FormField>
        <FormField label="转入账户" :error="transferErrors.to" :span="2">
          <select v-model="transferForm.to" class="select" :class="{ 'input--invalid': transferErrors.to }">
            <option :value="null" disabled>请选择转入账户</option>
            <option v-for="a in transferableOptions" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </FormField>
        <FormField label="金额（元）" :error="transferErrors.amount" :span="2">
          <input
            v-model="transferForm.amount"
            type="number"
            min="0"
            step="0.01"
            class="input"
            :class="{ 'input--invalid': transferErrors.amount }"
            placeholder="0.00"
          />
        </FormField>
        <FormField label="备注" :span="2">
          <input v-model="transferForm.remark" class="input" maxlength="100" placeholder="选填，如：微信充值到支付宝" />
        </FormField>
      </div>
      <template #footer>
        <button class="btn" :disabled="transferSaving" @click="transferOpen = false">取消</button>
        <button class="btn btn--primary" :disabled="transferSaving" @click="submitTransfer">
          {{ transferSaving ? '转账中…' : '确认转账' }}
        </button>
      </template>
    </BaseModal>

    <ConfirmDialog
      v-if="deleting"
      title="删除账户"
      :message="`删除账户「${deleting.name}」会同时删除使用该账户的所有账单，且无法恢复。确定删除吗？`"
      confirm-text="删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
    <p class="page-aphorism">流水不腐，户枢不蠹。</p>
  </div>
</template>
