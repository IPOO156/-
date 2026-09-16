import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { request, TOKEN_KEY } from '@/api/http'
import type { TokenResult } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) ?? '')
  const username = ref<string>(localStorage.getItem('bill_admin_username') ?? '')

  const isAuthed = computed(() => token.value !== '')

  async function login(user: string, password: string): Promise<void> {
    const res = await request<TokenResult>('/token/', {
      method: 'POST',
      form: true,
      body: { username: user, password },
      skipAuth: true,
    })
    token.value = res.token
    username.value = user
    localStorage.setItem(TOKEN_KEY, res.token)
    localStorage.setItem('bill_admin_username', user)
  }

  function logout(): void {
    token.value = ''
    username.value = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('bill_admin_username')
  }

  return { token, username, isAuthed, login, logout }
})
