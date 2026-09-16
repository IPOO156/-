<script setup lang="ts">
import BaseModal from './BaseModal.vue'

defineProps<{
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()
</script>

<template>
  <BaseModal small alert as-form :title="title" @close="emit('cancel')" @submit="emit('confirm')">
    <p class="confirm-message">{{ message }}</p>
    <template #footer>
      <button class="btn" type="button" :disabled="loading" @click="emit('cancel')">{{ cancelText ?? '取消' }}</button>
      <button
        class="btn"
        type="submit"
        :class="danger ? 'btn--danger' : 'btn--primary'"
        :disabled="loading"
      >
        <span v-if="loading" class="spinner" aria-hidden="true"></span>
        {{ confirmText ?? '确认' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.confirm-message {
  color: var(--c-text-secondary);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-line;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid oklch(0.985 0.005 85 / 0.35);
  border-top-color: var(--c-on-primary);
  border-radius: 9999px;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
