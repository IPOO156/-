<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'

const hasError = ref(false)

onErrorCaptured(() => {
  hasError.value = true
  // 阻止继续向父级传播，避免整棵组件树白屏
  return false
})

function reload(): void {
  window.location.reload()
}
</script>

<template>
  <slot v-if="!hasError" />
  <div v-else class="error-fallback" role="alert">
    <div class="error-fallback-inner">
      <span class="seal" aria-hidden="true">记</span>
      <h1>出错了</h1>
      <p>页面遇到异常，请刷新重试。</p>
      <button class="btn btn--primary" @click="reload">刷新页面</button>
    </div>
  </div>
</template>

<style scoped>
.error-fallback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--c-bg);
}

.error-fallback-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.error-fallback h1 {
  font-family: var(--font-display);
  font-size: 22px;
}

.error-fallback p {
  color: var(--c-text-secondary);
  font-size: 14px;
}
</style>
