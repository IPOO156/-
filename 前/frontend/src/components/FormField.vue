<script setup lang="ts">
/** 表单字段容器：标签 + 控件插槽 + 错误/提示。控件本身（input/select）由使用方经默认插槽传入 */
defineProps<{
  label?: string
  /** 控件下方的辅助提示 */
  hint?: string
  /** 校验错误文案（出现时覆盖 hint 展示） */
  error?: string
  /** 在 form-grid 中跨 2 列 */
  span?: 1 | 2
}>()
</script>

<template>
  <div class="field" :style="span === 2 ? 'grid-column: span 2' : undefined">
    <label v-if="label" class="field-label">{{ label }}</label>
    <slot />
    <span v-if="error" class="field-error" role="alert">{{ error }}</span>
    <span v-else-if="hint" class="field-hint">{{ hint }}</span>
  </div>
</template>
