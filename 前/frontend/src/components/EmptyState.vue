<script setup lang="ts">
import SvgIcon from './SvgIcon.vue'

defineProps<{ icon?: string; title?: string; desc?: string }>()
</script>

<template>
  <div class="empty">
    <div class="empty-icon">
      <SvgIcon :name="icon ?? 'inbox'" :size="24" />
    </div>
    <div v-if="title || $slots.default" class="empty-title">
      <slot>{{ title }}</slot>
    </div>
    <div v-if="desc" class="empty-desc">{{ desc }}</div>
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.empty-action {
  margin-top: 8px;
}
</style>
