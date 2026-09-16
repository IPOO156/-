import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'
import '@/assets/base.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

/** 任意接口返回 401（token 过期/失效）时全局登出并跳转登录页 */
window.addEventListener('bill:unauthorized', () => {
  const auth = useAuthStore()
  auth.logout()
  if (router.currentRoute.value.name !== 'login') {
    router.replace('/login')
  }
})

app.mount('#app')
