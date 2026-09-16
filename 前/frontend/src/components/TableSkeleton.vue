<script setup lang="ts">
/** 表格加载骨架屏（视觉占位，无语义） */
withDefaults(defineProps<{ rows?: number }>(), { rows: 3 })
</script>

<template>
  <div class="card loading-row" aria-hidden="true">
    <div v-for="n in rows" :key="n" class="skeleton"></div>
  </div>
</template>
