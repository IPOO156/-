import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    title?: string
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/',
      component: () => import('@/layouts/AdminLayout.vue'),
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '统计看板' } },
        { path: 'bills', name: 'bills', component: () => import('@/views/BillsView.vue'), meta: { title: '记账' } },
        { path: 'bills/recycle', name: 'recycle', component: () => import('@/views/RecycleBinView.vue'), meta: { title: '回收站' } },
        { path: 'accounts', name: 'accounts', component: () => import('@/views/AccountsView.vue'), meta: { title: '账户' } },
        { path: 'categories', name: 'categories', component: () => import('@/views/CategoriesView.vue'), meta: { title: '分类' } },
        { path: 'tags', name: 'tags', component: () => import('@/views/TagsView.vue'), meta: { title: '标签' } },
        { path: 'books', name: 'books', component: () => import('@/views/BooksView.vue'), meta: { title: '账本' } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.isAuthed && to.name === 'login') return { path: '/dashboard' }
    return true
  }
  if (!auth.isAuthed) return { path: '/login', query: to.fullPath === '/login' ? undefined : { redirect: to.fullPath } }
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 个人记账` : '个人记账'
})

export default router
