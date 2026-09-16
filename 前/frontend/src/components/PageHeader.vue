<script setup lang="ts">
/** 页面通用头部：标题 + 副题 + 落款 + 操作区（默认插槽） */
defineProps<{
  title: string
  sub?: string
  dateline?: string
}>()
</script>

<template>
  <div class="page-head">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="sub" class="page-sub">{{ sub }}</p>
      <p v-if="dateline" class="dateline">{{ dateline }}</p>
    </div>
    <div v-if="$slots.default" class="head-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: none;
}
</style>
