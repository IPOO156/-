<script setup lang="ts">
import { useToastStore } from '@/stores/toast'
import SvgIcon from './SvgIcon.vue'

const store = useToastStore()
</script>

<template>
  <Teleport to="body">
    <div class="toast-host">
      <TransitionGroup name="toast">
        <div
          v-for="t in store.toasts"
          :key="t.id"
          class="toast"
          :class="`toast--${t.type}`"
          role="alert"
        >
          <SvgIcon
            v-if="t.type === 'success'"
            name="check"
            :size="16"
            style="color: var(--c-success)"
          />
          <SvgIcon
            v-else-if="t.type === 'error'"
            name="warning"
            :size="16"
            style="color: var(--c-danger)"
          />
          <span>{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding-top: 14px;
  padding-bottom: 14px;
  line-height: 1.5;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
