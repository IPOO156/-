<script setup lang="ts">
import ToastHost from '@/components/ToastHost.vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
</script>

<template>
  <div class="grain" aria-hidden="true"></div>
  <ErrorBoundary>
    <RouterView v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </ErrorBoundary>
  <ToastHost />
</template>
