<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { ApiError } from '@/api/http'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const auth = useAuthStore()
const bookStore = useBookStore()
const toast = useToast()

const navItems = [
  { path: '/dashboard', label: '统计看板', icon: 'dashboard' },
  { path: '/bills', label: '记账', icon: 'bill' },
  { path: '/bills/recycle', label: '回收站', icon: 'restore' },
  { path: '/accounts', label: '账户', icon: 'wallet' },
  { path: '/categories', label: '分类', icon: 'category' },
  { path: '/tags', label: '标签', icon: 'tag' },
  { path: '/books', label: '账本', icon: 'book' },
]

const hasBooks = computed(() => bookStore.books.length > 0)

function onBookChange(e: Event): void {
  const val = Number((e.target as HTMLSelectElement).value)
  if (val) bookStore.setCurrentBook(val)
}

function onLogout(): void {
  auth.logout()
  bookStore.reset()
  router.replace('/login')
}

onMounted(async () => {
  try {
    await bookStore.fetchBooks()
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      auth.logout()
      router.replace('/login')
    } else {
      // 加载失败也要结束加载态，避免账本选择器一直显示骨架
      bookStore.loaded = true
      toast.error(e instanceof ApiError ? e.message : '账本加载失败')
    }
  }
})
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <router-link to="/dashboard" class="brand">
        <span class="seal" aria-hidden="true">记</span>
        <span class="brand-name">个人记账</span>
      </router-link>

      <nav class="nav">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          <SvgIcon :name="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-foot">
        <p class="sidebar-quote">日清月结 · 心里有数</p>
        <div class="sidebar-user">
          <span class="avatar">{{ (auth.username || 'U').slice(0, 1).toUpperCase() }}</span>
          <div class="sidebar-user-meta">
            <span class="on-dark">{{ auth.username || '用户' }}</span>
            <button class="logout-link" @click="onLogout">
              <SvgIcon name="logout" :size="13" />
              退出登录
            </button>
          </div>
        </div>
      </div>

      <span class="vertical-text" aria-hidden="true">收支 · 明细 · 账目</span>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <div class="book-switch">
            <span class="book-chip">
              <SvgIcon name="book" :size="15" style="color: var(--c-primary)" />
              <select
                v-if="bookStore.loaded && hasBooks"
                class="book-select"
                :value="bookStore.currentBookId ?? ''"
                aria-label="切换账本"
                @change="onBookChange"
              >
                <option v-for="b in bookStore.books" :key="b.id" :value="b.id">
                  {{ b.name }}{{ b.is_archived ? '（已归档）' : '' }}
                </option>
              </select>
              <router-link v-else-if="bookStore.loaded" to="/books" class="book-empty-link"
                >请先创建账本</router-link
              >
              <span v-else class="skeleton book-skeleton" aria-hidden="true"></span>
            </span>
          </div>
        </div>

        <div class="topbar-right">
          <router-link to="/books" class="btn btn--ghost btn--sm">
            <SvgIcon name="plus" :size="15" />
            账本
          </router-link>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

/* ---------- 暖棕侧栏（羊皮账本质感，实色无渐变） ---------- */
.sidebar {
  flex: none;
  width: 232px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 26px 14px 20px;
  background: var(--c-nav-bg);
  border-right: 1px solid var(--c-nav-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 4px 10px;
  color: var(--c-on-nav);
}

.brand-name {
  font-family: var(--font-kai);
  font-size: 19px;
  letter-spacing: 0.14em;
  color: var(--c-on-nav);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 46px;
  padding: 0 14px;
  border-radius: 10px;
  color: var(--c-nav-text);
  font-size: 14px;
  font-weight: 500;
  transition: background 0.16s, color 0.16s, transform 0.09s;
}

.nav-item:hover {
  background: oklch(0.9 0.02 80 / 0.1);
  color: var(--c-nav-hover);
}

.nav-item:active {
  transform: scale(0.98);
}

.nav-item.router-link-active {
  background: var(--c-primary);
  color: var(--c-on-primary);
  font-weight: 600;
  box-shadow: var(--shadow-primary);
}

.sidebar-foot {
  margin-top: auto;
  padding: 16px 10px 0;
  border-top: 1px solid var(--c-nav-border);
}

.sidebar-quote {
  margin-bottom: 12px;
  font-family: var(--font-display);
  font-size: 12.5px;
  letter-spacing: 0.14em;
  color: var(--c-nav-muted);
}

.vertical-text {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  font-family: var(--font-display);
  letter-spacing: 0.3em;
  font-size: 11px;
  color: oklch(0.9 0.02 80 / 0.42);
  pointer-events: none;
}

.sidebar {
  position: relative;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9999px;
  background: var(--c-primary);
  color: var(--c-on-primary);
  font-size: 14px;
  font-weight: 700;
}

.sidebar-user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.logout-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: none;
  background: none;
  color: var(--c-nav-muted);
  font-size: 12px;
  cursor: pointer;
  transition: color 0.15s;
}

.logout-link:hover {
  color: var(--c-nav-hover);
}

/* ---------- 头部（暖色实底，无毛玻璃） ---------- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 24px;
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.book-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
}

.book-select {
  min-height: 44px;
  max-width: 240px;
  padding: 0 32px 0 6px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  background: var(--c-surface);
  color: var(--c-text);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-soft);
}

.book-empty-link {
  color: var(--c-primary);
  font-size: 14px;
  font-weight: 600;
}

.book-skeleton {
  width: 140px;
  height: 40px;
}

.content {
  flex: 1;
}

@media (max-width: 860px) {
  .layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    flex-direction: row;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-right: none;
    border-bottom: 1px solid var(--c-nav-border);
    overflow-x: auto;
  }

  .brand-name,
  .sidebar-foot {
    display: none;
  }

  .brand {
    padding: 0;
  }

  .nav {
    flex-direction: row;
    gap: 4px;
    flex: 1;
  }

  .nav-item {
    min-height: 40px;
    white-space: nowrap;
    padding: 0 12px;
  }

  .topbar {
    flex-wrap: wrap;
  }
}
</style>
