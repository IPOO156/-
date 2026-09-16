<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ percent: number; over?: boolean }>(), { percent: 0 })

const width = computed(() => `${Math.min(100, Math.max(0, props.percent))}%`)
</script>

<template>
  <div class="progress" role="progressbar" :aria-valuenow="percent" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-fill" :class="{ 'is-over': over }" :style="{ width }"></div>
  </div>
</template>
