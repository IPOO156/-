<script setup lang="ts">
import { ref, watch } from 'vue'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { useServerPagination } from '@/composables/useServerPagination'
import { billApi } from '@/api/bill'
import { ApiError } from '@/api/http'
import { fmtDateTime, money } from '@/utils/format'
import { billAmountClass, billSign, billTypePill } from '@/utils/billType'
import type { Bill } from '@/types/api'
import SvgIcon from '@/components/SvgIcon.vue'
import PageHeader from '@/components/PageHeader.vue'
import TableSkeleton from '@/components/TableSkeleton.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const bookStore = useBookStore()
const toast = useToast()

const items = ref<Bill[]>([])
const loading = ref(false)
const { page, size, total, pages, go, setSize, setTotal, reset } = useServerPagination(20)

async function loadData(): Promise<void> {
  const bookId = bookStore.currentBook?.id
  if (!bookId) {
    items.value = []
    setTotal(0)
    return
  }
  loading.value = true
  try {
    const res = await billApi.recycleBin({
      book: bookId,
      page: page.value,
      size: size.value,
    })
    items.value = res.results
    setTotal(res.count)
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '回收站加载失败')
  } finally {
    loading.value = false
  }
}

async function restore(bill: Bill): Promise<void> {
  try {
    await billApi.restore(bill.id)
    items.value = items.value.filter((b) => b.id !== bill.id)
    setTotal(total.value - 1)
    toast.success('已恢复，账户余额已更新')
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '恢复失败')
  }
}

const deleting = ref<Bill | null>(null)
const deleteLoading = ref(false)

async function confirmPermanentDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await billApi.permanentDelete(deleting.value.id)
    items.value = items.value.filter((b) => b.id !== deleting.value!.id)
    setTotal(total.value - 1)
    toast.success('已彻底删除')
    deleting.value = null
  } catch (e) {
    toast.error(e instanceof ApiError ? e.message : '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

function onPageChange(p: number): void {
  go(p)
  void loadData()
}

function onSizeChange(v: number): void {
  setSize(v)
  void loadData()
}

// 随当前账本切换自动刷新（区别于旧实现的「仅挂载时加载」）
watch(
  () => bookStore.currentBook?.id,
  () => {
    reset()
    void loadData()
  },
  { immediate: true },
)
</script>

<template>
  <div class="page" style="--page-char: '拾'">
    <PageHeader
      title="回收站"
      sub="删去的账单暂存于此，可召回，亦可永除。"
      :dateline="`回收站内 ${total} 条记录 · 彻底删除后不可恢复`"
    >
      <button class="btn" :disabled="loading" @click="loadData">
        <SvgIcon name="refresh" :size="15" />
        刷新
      </button>
    </PageHeader>

    <TableSkeleton v-if="loading" />

    <EmptyState
      v-else-if="total === 0"
      icon="restore"
      title="回收站是空的"
      desc="删除的账单会出现在这里，可恢复或彻底清除。"
    />

    <template v-else>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th class="th-index">No.</th>
              <th>发生时间</th>
              <th>类型</th>
              <th>金额</th>
              <th>账户</th>
              <th>备注</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(b, i) in items" :key="b.id">
              <td class="th-index"><span class="row-index">{{ (page - 1) * size + i + 1 }}</span></td>
              <td class="muted">{{ fmtDateTime(b.occurred_at) }}</td>
              <td><span class="pill" :class="billTypePill(b.type)">{{ b.type_display }}</span></td>
              <td class="num">
                <span :class="billAmountClass(b.type)">
                  {{ billSign(b.type) }}¥{{ money(b.amount) }}
                </span>
              </td>
              <td class="muted">
                {{ b.account_name }}<template v-if="b.type === 'transfer' && b.to_account_name"> → {{ b.to_account_name }}</template>
              </td>
              <td class="muted">{{ b.remark || '—' }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn--ghost btn--sm" @click="restore(b)">
                    <SvgIcon name="restore" :size="15" />
                    恢复
                  </button>
                  <button class="btn btn--danger-outline btn--sm" @click="deleting = b">
                    <SvgIcon name="trash" :size="15" />
                    彻底删除
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
        @update:page="onPageChange"
        @update:size="onSizeChange"
      />
    </template>

    <ConfirmDialog
      v-if="deleting"
      title="彻底删除"
      :message="`彻底删除这条${deleting.type_display}（¥${money(deleting.amount)}）后无法恢复，确定吗？`"
      confirm-text="彻底删除"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmPermanentDelete"
    />
    <p class="page-aphorism">覆水难收，慎始慎终。</p>
  </div>
</template>
