<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PieItem } from '@/types/api'
import { fmtPercent, money, toNumber } from '@/utils/format'
import { CATEGORY_COLORS } from '@/utils/constants'

const props = defineProps<{ items: PieItem[]; typeLabel?: string }>()

const SIZE = 176
const STROKE = 24
const R = (SIZE - STROKE) / 2 - 4
const CIRC = 2 * Math.PI * R
const CENTER = SIZE / 2

const FALLBACK_COLORS = CATEGORY_COLORS

const activeIdx = ref<number | null>(null)

const total = computed(() => props.items.reduce((s, it) => s + toNumber(it.total), 0))

interface Seg extends PieItem {
  start: number
  frac: number
  idx: number
}

const segments = computed<Seg[]>(() => {
  let acc = 0
  return props.items.map((it, idx) => {
    const v = toNumber(it.total)
    const frac = total.value > 0 ? v / total.value : 0
    const seg: Seg = { ...it, start: acc, frac, idx }
    acc += frac
    return seg
  })
})

function colorOf(seg: Seg): string {
  return seg.color || FALLBACK_COLORS[seg.idx % FALLBACK_COLORS.length]!
}
</script>

<template>
  <div v-if="items.length === 0" class="chart-empty">
    当前时段暂无{{ typeLabel ?? '支出' }}记录，去记一笔看看
  </div>
  <div v-else class="chart-pie">
    <div class="chart-canvas">
      <svg :width="SIZE" :height="SIZE" viewBox="0 0 176 176" role="img" aria-label="分类占比饼图">
        <g :transform="`rotate(-90 ${CENTER} ${CENTER})`">
          <circle :cx="CENTER" :cy="CENTER" :r="R" fill="none" style="stroke: var(--c-border)" :stroke-width="STROKE" />
          <circle
            v-for="s in segments"
            :key="s.idx"
            class="pie-seg seg-fade"
            :cx="CENTER"
            :cy="CENTER"
            :r="R"
            fill="none"
            :stroke="colorOf(s)"
            :stroke-width="STROKE"
            :stroke-dasharray="`${s.frac * CIRC} ${CIRC}`"
            :stroke-dashoffset="-s.start * CIRC"
            :opacity="activeIdx === null || activeIdx === s.idx ? 1 : 0.35"
            :style="{ animationDelay: `${s.idx * 90}ms` }"
            @mouseenter="activeIdx = s.idx"
            @mouseleave="activeIdx = null"
          >
            <title>{{ s.category_name ?? '未分类' }}：¥{{ money(s.total) }}</title>
          </circle>
        </g>
      </svg>
      <div class="chart-center">
        <div class="chart-center-label">{{ typeLabel ?? '支出' }}合计</div>
        <div class="chart-center-value">¥{{ money(total) }}</div>
      </div>
    </div>
    <ul class="chart-legend">
      <li
        v-for="s in segments"
        :key="s.idx"
        class="legend-row"
        @mouseenter="activeIdx = s.idx"
        @mouseleave="activeIdx = null"
      >
        <span class="dot" :style="{ background: colorOf(s) }"></span>
        <span class="legend-name" :title="s.category_name ?? ''">{{ s.category_name ?? '未分类' }}</span>
        <span class="legend-percent">{{ fmtPercent(s.percent) }}</span>
        <span class="legend-total">¥{{ money(s.total) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.chart-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--c-text-faint);
  font-size: 13px;
}

.chart-pie {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.chart-canvas {
  position: relative;
  flex: none;
}

.chart-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.chart-center-label {
  font-size: 12px;
  color: var(--c-text-faint);
}

.chart-center-value {
  font-size: 18px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.pie-seg {
  transition: opacity 0.15s;
  cursor: pointer;
}

.chart-legend {
  flex: 1;
  min-width: 180px;
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
}

.legend-row:hover {
  background: var(--c-row-hover);
}

.legend-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text);
}

.legend-percent {
  color: var(--c-text-secondary);
}

.legend-total {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
</style>
