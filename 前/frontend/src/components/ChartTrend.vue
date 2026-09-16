<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { TrendItem } from '@/types/api'
import { money0, toNumber } from '@/utils/format'

const props = defineProps<{ items: TrendItem[] }>()

const W = 640
const H = 300
const PAD = { l: 54, r: 16, t: 26, b: 32 }
const INNER_W = W - PAD.l - PAD.r
const INNER_H = H - PAD.t - PAD.b

const max = computed(() => {
  let m = 0
  for (const it of props.items) {
    m = Math.max(m, toNumber(it.expense), toNumber(it.income))
  }
  return m || 1
})

function x(i: number): number {
  const n = props.items.length
  if (n <= 1) return PAD.l + INNER_W / 2
  return PAD.l + (i / (n - 1)) * INNER_W
}

function y(v: number): number {
  return PAD.t + (1 - v / max.value) * INNER_H
}

/** Catmull-Rom → 贝塞尔平滑曲线 */
function smooth(points: [number, number][]): string {
  if (points.length === 0) return ''
  if (points.length === 1) return `M ${points[0]![0]},${points[0]![1]}`
  let d = `M ${points[0]![0]},${points[0]![1]}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] ?? points[i]!
    const p1 = points[i]!
    const p2 = points[i + 1]!
    const p3 = points[i + 2] ?? p2
    const c1x = p1[0] + (p2[0] - p0[0]) / 6
    const c1y = p1[1] + (p2[1] - p0[1]) / 6
    const c2x = p2[0] - (p3[0] - p1[0]) / 6
    const c2y = p2[1] - (p3[1] - p1[1]) / 6
    d += ` C ${c1x},${c1y} ${c2x},${c2y} ${p2[0]},${p2[1]}`
  }
  return d
}

const ptsIncome = computed(() => props.items.map((it, i) => [x(i), y(toNumber(it.income))] as [number, number]))
const ptsExpense = computed(() => props.items.map((it, i) => [x(i), y(toNumber(it.expense))] as [number, number]))

const lineIncome = computed(() => smooth(ptsIncome.value))
const lineExpense = computed(() => smooth(ptsExpense.value))

const n = computed(() => props.items.length)

function areaPath(line: string): string {
  if (!line || n.value === 0) return ''
  const last = x(n.value - 1)
  const first = x(0)
  return `${line} L ${last},${y(0)} L ${first},${y(0)} Z`
}

const areaIncome = computed(() => areaPath(lineIncome.value))
const areaExpense = computed(() => areaPath(lineExpense.value))

const GRID = [0, 0.25, 0.5, 0.75, 1]

/* 响应式 x 轴标签：按容器宽度决定可容纳的标签数，窄屏自动减密度 */
const wrapEl = ref<HTMLElement | null>(null)
const chartWidth = ref(0)
let ro: ResizeObserver | null = null

onMounted(() => {
  ro = new ResizeObserver((entries) => {
    chartWidth.value = entries[0]?.contentRect.width ?? 0
  })
  if (wrapEl.value) ro.observe(wrapEl.value)
})

onUnmounted(() => ro?.disconnect())

const labelIndices = computed(() => {
  const count = n.value
  if (count === 0) return []
  // 每个日期标签至少约 38px 才不重叠；桌面不超过 6 个
  const maxLabels =
    chartWidth.value > 0 ? Math.max(2, Math.min(6, Math.floor(chartWidth.value / 38))) : 6
  const k = Math.min(count, maxLabels)
  if (count <= k) return props.items.map((_, i) => i)
  const step = (count - 1) / (k - 1)
  return Array.from({ length: k }, (_, i) => Math.round(i * step))
})

interface Mark {
  cx: number
  cy: number
  color: string
  label: string
  showLabel: boolean
}

/** 非零数据点：加粗标记 + 关键点数值标注 */
const marks = computed<Mark[]>(() => {
  const list: Mark[] = []
  const nzIncome = props.items
    .map((it, i) => ({ i, v: toNumber(it.income) }))
    .filter((m) => m.v > 0)
  const nzExpense = props.items
    .map((it, i) => ({ i, v: toNumber(it.expense) }))
    .filter((m) => m.v > 0)

  const topIncome = new Set(nzIncome.slice().sort((a, b) => b.v - a.v).slice(0, 3).map((m) => m.i))
  const topExpense = new Set(nzExpense.slice().sort((a, b) => b.v - a.v).slice(0, 3).map((m) => m.i))
  const labelAll = nzIncome.length + nzExpense.length <= 6

  for (const m of nzIncome) {
    list.push({
      cx: x(m.i),
      cy: y(m.v),
      color: 'var(--c-success)',
      label: `¥${money0(m.v)}`,
      showLabel: labelAll || topIncome.has(m.i),
    })
  }
  for (const m of nzExpense) {
    list.push({
      cx: x(m.i),
      cy: y(m.v),
      color: 'var(--c-danger)',
      label: `¥${money0(m.v)}`,
      showLabel: labelAll || topExpense.has(m.i),
    })
  }
  return list
})

function shortDate(d: string): string {
  return d.length >= 10 ? d.slice(5) : d
}
</script>

<template>
  <div v-if="items.length === 0" class="chart-empty">当前时段暂无收支记录</div>
  <div v-else ref="wrapEl" class="chart-wrap">
    <div class="chart-legend">
      <span class="legend-item"><span class="legend-line" style="background: var(--c-success)"></span>收入</span>
      <span class="legend-item"><span class="legend-line" style="background: var(--c-danger)"></span>支出</span>
    </div>
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      class="chart-svg"
      role="img"
      aria-label="收支趋势折线图，绿色为收入，红色为支出"
    >
      <defs>
        <linearGradient id="gInc" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" style="stop-color: var(--c-success)" stop-opacity="0.22" />
          <stop offset="100%" style="stop-color: var(--c-success)" stop-opacity="0" />
        </linearGradient>
        <linearGradient id="gExp" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" style="stop-color: var(--c-danger)" stop-opacity="0.18" />
          <stop offset="100%" style="stop-color: var(--c-danger)" stop-opacity="0" />
        </linearGradient>
      </defs>

      <!-- 网格 + 坐标 -->
      <g v-for="(g, gi) in GRID" :key="gi">
        <line
          :x1="PAD.l"
          :x2="W - PAD.r"
          :y1="y(max * g)"
          :y2="y(max * g)"
          :stroke="g === 0 ? 'var(--c-border-strong)' : 'var(--c-border)'"
          :stroke-width="g === 0 ? 1.4 : 1"
          stroke-dasharray="none"
        />
        <text :x="PAD.l - 9" :y="y(max * g) + 4" text-anchor="end" class="axis-label">
          {{ gi === 0 ? 0 : money0(max * g) }}
        </text>
      </g>

      <!-- 面积 -->
      <path v-if="areaIncome" :d="areaIncome" fill="url(#gInc)" />
      <path v-if="areaExpense" :d="areaExpense" fill="url(#gExp)" />

      <!-- 平滑曲线 -->
      <path
        v-if="lineIncome"
        :d="lineIncome"
        fill="none"
        style="stroke: var(--c-success)"
        stroke-width="3"
        stroke-linecap="round"
        pathLength="1"
        class="line-draw"
      />
      <path
        v-if="lineExpense"
        :d="lineExpense"
        fill="none"
        style="stroke: var(--c-danger)"
        stroke-width="3"
        stroke-linecap="round"
        pathLength="1"
        class="line-draw"
        :style="{ animationDelay: '0.25s' }"
      />

      <!-- 数据点 + 数值标注 -->
      <g v-for="(m, i) in marks" :key="i">
        <circle :cx="m.cx" :cy="m.cy" r="4.5" :style="{ fill: m.color }" stroke="var(--c-surface)" stroke-width="1.6">
          <title>{{ m.label }}</title>
        </circle>
        <text v-if="m.showLabel" :x="m.cx" :y="m.cy - 11" text-anchor="middle" class="mark-label" :style="{ fill: m.color }">
          {{ m.label }}
        </text>
      </g>

      <!-- 日期标签 -->
      <text
        v-for="i in labelIndices"
        :key="i"
        :x="x(i)"
        :y="H - 8"
        text-anchor="middle"
        class="axis-label"
      >
        {{ shortDate(items[i]!.date) }}
      </text>
    </svg>
  </div>
</template>

<style scoped>
.chart-empty {
  padding: 56px 16px;
  text-align: center;
  color: var(--c-text-faint);
  font-family: var(--font-kai);
  font-size: 13px;
  letter-spacing: 0.08em;
}

.chart-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chart-legend {
  display: flex;
  align-items: center;
  gap: 18px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  color: var(--c-text-secondary);
}

.legend-line {
  width: 22px;
  height: 3px;
  border-radius: 9999px;
  display: inline-block;
}

.chart-svg {
  width: 100%;
  height: auto;
  max-height: 300px;
  overflow: visible;
}

.axis-label {
  font-size: 11px;
  fill: var(--c-text-faint);
  font-variant-numeric: tabular-nums;
}

.mark-label {
  font-size: 10.5px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
}
</style>
