import { useToastStore, type ToastType } from '@/stores/toast'

export function useToast() {
  const store = useToastStore()
  return {
    success: (m: string) => store.push('success', m),
    error: (m: string) => store.push('error', m),
    info: (m: string) => store.push('info', m),
  }
}

export type { ToastType }
