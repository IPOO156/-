<script setup lang="ts">
import { computed } from 'vue'
import SvgIcon from './SvgIcon.vue'

const props = defineProps<{
  page: number
  size: number
  total: number
  pages: number
}>()

const emit = defineEmits<{
  'update:page': [number]
  'update:size': [number]
}>()

const PAGE_SIZES = [10, 20, 50]

const pageList = computed<number[]>(() => {
  const p = props.pages
  const cur = props.page
  if (p <= 7) return Array.from({ length: p }, (_, i) => i + 1)
  const set = new Set<number>([1, p, cur - 1, cur, cur + 1])
  const sorted = [...set].filter((n) => n >= 1 && n <= p).sort((a, b) => a - b)
  const out: number[] = []
  let prev = 0
  for (const n of sorted) {
    if (n - prev > 1) out.push(-1)
    out.push(n)
    prev = n
  }
  return out
})

function go(p: number): void {
  if (p >= 1 && p <= props.pages) emit('update:page', p)
}
</script>

<template>
  <div class="pagination">
    <div class="pagination-info">
      共 {{ total }} 条 · 第 {{ page }}/{{ pages }} 页
    </div>
    <div class="pagination-actions">
      <select
        class="pagination-size"
        :value="size"
        aria-label="每页条数"
        @change="emit('update:size', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="s in PAGE_SIZES" :key="s" :value="s">{{ s }} 条/页</option>
      </select>
      <button class="pagination-btn" :disabled="page <= 1" aria-label="上一页" @click="go(page - 1)">
        <SvgIcon name="chevronLeft" :size="16" />
      </button>
      <template v-for="(n, i) in pageList" :key="i">
        <span v-if="n === -1" class="faint" style="padding: 0 4px">…</span>
        <button
          v-else
          class="pagination-btn"
          :class="{ 'is-active': n === page }"
          :aria-current="n === page ? 'page' : undefined"
          @click="go(n)"
        >
          {{ n }}
        </button>
      </template>
      <button
        class="pagination-btn"
        :disabled="page >= pages"
        aria-label="下一页"
        @click="go(page + 1)"
      >
        <SvgIcon name="chevronRight" :size="16" />
      </button>
    </div>
  </div>
</template>
