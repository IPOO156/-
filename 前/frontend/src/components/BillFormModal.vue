<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { billApi } from '@/api/bill'
import { ApiError } from '@/api/http'
import { useToast } from '@/composables/useToast'
import { fromDatetimeLocal, toDatetimeLocal, toNumber } from '@/utils/format'
import { BILL_TYPES } from '@/utils/constants'
import type { Account, Bill, BillType, Category, Tag } from '@/types/api'
import SvgIcon from './SvgIcon.vue'
import BaseModal from './BaseModal.vue'
import FormField from './FormField.vue'

const props = defineProps<{
  isEdit: boolean
  bookId: number
  bill: Bill | null
  categories: Category[]
  accounts: Account[]
  tags: Tag[]
}>()

const emit = defineEmits<{ close: []; saved: [] }>()
const toast = useToast()

const form = reactive<{
  type: BillType
  amount: string
  occurred_at: string
  category: number | null
  account: number | null
  to_account: number | null
  remark: string
  tags: number[]
}>({
  type: props.bill?.type ?? 'expense',
  amount: props.bill ? String(toNumber(props.bill.amount)) : '',
  occurred_at: props.bill ? toDatetimeLocal(props.bill.occurred_at) : toDatetimeLocal(new Date().toISOString()),
  category: props.bill?.category ?? null,
  account: props.bill?.account ?? null,
  to_account: props.bill?.to_account ?? null,
  remark: props.bill?.remark ?? '',
  tags: props.bill ? [...props.bill.tags] : [],
})

const saving = ref(false)
const formErrors = reactive<Record<string, string>>({})

const formCategories = computed<Category[]>(() =>
  props.categories.filter((c) => c.type === form.type && c.is_active),
)

/** 可选账户：启用账户 + 当前账单已选账户（可能已停用） */
const formAccounts = computed(() => {
  const act = props.accounts.filter((a) => a.is_active)
  const need = props.isEdit ? [form.account, form.to_account] : []
  const extra = props.accounts.filter((a) => !a.is_active && need.includes(a.id))
  const merged = [...act, ...extra]
  return Array.from(new Map(merged.map((a) => [a.id, a])).values())
})

const transferableAccounts = computed(() => formAccounts.value.filter((a) => a.id !== form.account))

function setType(t: BillType): void {
  form.type = t
  if (t === 'transfer') form.category = null
  else form.to_account = null
}

function toggleTag(id: number): void {
  form.tags = form.tags.includes(id) ? form.tags.filter((t) => t !== id) : [...form.tags, id]
}

function validate(): boolean {
  formErrors.amount = ''
  formErrors.occurred_at = ''
  formErrors.category = ''
  formErrors.account = ''
  formErrors.to_account = ''

  const amount = Number(form.amount)
  if (form.amount === '' || Number.isNaN(amount) || amount <= 0) formErrors.amount = '请输入大于 0 的金额'
  if (!form.occurred_at) formErrors.occurred_at = '请选择发生时间'
  if (form.type !== 'transfer' && form.category === null) formErrors.category = '请选择分类'
  if (form.account === null) formErrors.account = '请选择账户'
  if (form.type === 'transfer') {
    if (form.to_account === null) formErrors.to_account = '请选择转入账户'
    else if (form.to_account === form.account) formErrors.to_account = '转入账户不能与转出账户相同'
  }
  if (form.remark.trim().length > 500) formErrors.remark = '备注不能超过 500 字'
  return !Object.values(formErrors).some(Boolean)
}

async function onSubmit(): Promise<void> {
  if (!validate() || saving.value) return
  saving.value = true
  try {
    const payload = {
      book: props.bookId,
      type: form.type,
      amount: Number(form.amount),
      occurred_at: fromDatetimeLocal(form.occurred_at),
      category: form.type === 'transfer' ? null : form.category,
      account: form.account as number,
      to_account: form.type === 'transfer' ? form.to_account : null,
      remark: form.remark.trim(),
      tags: form.tags,
    }
    if (props.isEdit && props.bill) await billApi.update(props.bill.id, payload)
    else await billApi.create(payload)
    toast.success(props.isEdit ? '账单已更新，账户余额已重算' : '账单已记录，账户余额已更新')
    emit('saved')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <BaseModal :title="isEdit ? '编辑账单' : '记一笔'" width="640px" @close="emit('close')">
    <div class="form-grid">
      <FormField label="类型" :span="2">
        <div class="segmented form-type">
          <button
            v-for="t in BILL_TYPES"
            :key="t.value"
            type="button"
            class="segmented-item"
            :class="{ 'is-active': form.type === t.value }"
            @click="setType(t.value)"
          >
            {{ t.label }}
          </button>
        </div>
      </FormField>

      <FormField label="金额（元）（必填）" :error="formErrors.amount">
        <input
          v-model="form.amount"
          type="number"
          min="0"
          step="0.01"
          class="input"
          :class="{ 'input--invalid': formErrors.amount }"
          placeholder="0.00"
        />
      </FormField>

      <FormField label="发生时间" :error="formErrors.occurred_at">
        <input
          v-model="form.occurred_at"
          type="datetime-local"
          class="input"
          :class="{ 'input--invalid': formErrors.occurred_at }"
        />
      </FormField>

      <FormField v-if="form.type !== 'transfer'" label="分类（必填）" :error="formErrors.category" :span="2">
        <select
          v-model="form.category"
          class="select"
          :class="{ 'input--invalid': formErrors.category }"
        >
          <option :value="null" disabled>请选择分类</option>
          <option v-for="c in formCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </FormField>

      <FormField :label="form.type === 'transfer' ? '转出账户' : '账户'" :error="formErrors.account" :span="2">
        <select
          v-model="form.account"
          class="select"
          :class="{ 'input--invalid': formErrors.account }"
        >
          <option :value="null" disabled>请选择账户</option>
          <option v-for="a in formAccounts" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </FormField>

      <FormField v-if="form.type === 'transfer'" label="转入账户" :error="formErrors.to_account" :span="2">
        <select
          v-model="form.to_account"
          class="select"
          :class="{ 'input--invalid': formErrors.to_account }"
        >
          <option :value="null" disabled>请选择转入账户</option>
          <option v-for="a in transferableAccounts" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </FormField>

      <FormField label="备注（≤500 字）" :error="formErrors.remark" :span="2">
        <textarea v-model="form.remark" class="textarea" maxlength="500" placeholder="选填"></textarea>
      </FormField>

      <FormField label="标签（可多选）" :span="2">
        <div v-if="tags.length" class="tag-check">
          <button
            v-for="t in tags"
            :key="t.id"
            type="button"
            class="tag-check-item"
            :class="{ 'is-selected': form.tags.includes(t.id) }"
            @click="toggleTag(t.id)"
          >
            <span class="dot" :style="{ background: t.color || 'var(--c-border-strong)' }"></span>
            {{ t.name }}
          </button>
        </div>
        <p v-else class="field-hint">还没有标签，可去「标签」页创建。</p>
      </FormField>
    </div>

    <template #footer>
      <button class="btn" :disabled="saving" @click="emit('close')">取消</button>
      <button class="btn btn--primary" :disabled="saving" @click="onSubmit">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.form-type {
  width: 100%;
}

.form-type .segmented-item {
  flex: 1;
  min-height: 44px;
  justify-content: center;
}
</style>
