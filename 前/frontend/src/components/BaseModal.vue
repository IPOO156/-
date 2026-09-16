<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'
import SvgIcon from './SvgIcon.vue'

const props = defineProps<{
  title?: string
  width?: string
  small?: boolean
  /** 确认类弹窗：role 提升为 alertdialog，语义告知屏幕阅读器需立即处理 */
  alert?: boolean
  /** 以 <form> 包裹 body/footer，支持回车提交；确认按钮应设为 type="submit" */
  asForm?: boolean
}>()

const emit = defineEmits<{ close: []; submit: [] }>()

const panel = ref<HTMLElement | null>(null)
const titleId = useId()

// 焦点恢复：记住打开前的焦点元素
let previousFocus: HTMLElement | null = null
// 滚动锁：记住打开前的 body overflow
let previousOverflow = ''

onMounted(() => {
  previousFocus = document.activeElement as HTMLElement | null
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKeydown)
  panel.value?.focus({ preventScroll: true })
  // asForm 弹窗：默认聚焦主提交按钮，打开即支持回车确认
  if (props.asForm) {
    panel.value?.querySelector<HTMLElement>('button[type="submit"]')?.focus({ preventScroll: true })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = previousOverflow
  previousFocus?.focus({ preventScroll: true })
})

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  // 简易焦点陷阱：Tab 在弹窗内循环，避免焦点落到背景页面
  if (e.key !== 'Tab') return
  const root = panel.value
  if (!root) return
  const focusables = root.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  )
  if (focusables.length === 0) return
  const first = focusables[0]!
  const last = focusables[focusables.length - 1]!
  const active = document.activeElement as HTMLElement | null
  if (e.shiftKey) {
    if (active === first || !root.contains(active)) {
      e.preventDefault()
      last.focus()
    }
  } else if (active === last || !root.contains(active)) {
    e.preventDefault()
    first.focus()
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @mousedown.self="emit('close')">
      <div
        ref="panel"
        class="modal-panel"
        :class="{ 'modal-panel--sm': small }"
        :style="width ? { maxWidth: width } : undefined"
        :role="alert ? 'alertdialog' : 'dialog'"
        :aria-modal="'true'"
        :aria-labelledby="title ? titleId : undefined"
        tabindex="-1"
      >
        <div v-if="title || $slots.head" class="modal-head">
          <h3 :id="titleId" class="modal-title orn-diamond">{{ title }}</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="emit('close')">
            <SvgIcon name="close" :size="18" />
          </button>
        </div>
        <form v-if="asForm" @submit.prevent="emit('submit')">
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-foot">
            <slot name="footer" />
          </div>
        </form>
        <template v-else>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-foot">
            <slot name="footer" />
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
