<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBookStore } from '@/stores/book'
import { useToast } from '@/composables/useToast'
import { ApiError } from '@/api/http'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const bookStore = useBookStore()
const toast = useToast()

// 默认不预填用户名；记住上次登录的账号方便下次输入
const form = reactive({ username: localStorage.getItem('bill_admin_username') ?? '', password: '' })
const submitting = ref(false)
const usernameError = ref('')
const passwordError = ref('')

function validate(): boolean {
  usernameError.value = form.username.trim() ? '' : '请输入用户名'
  passwordError.value = form.password ? '' : '请输入密码'
  return !usernameError.value && !passwordError.value
}

async function onSubmit(): Promise<void> {
  if (submitting.value || !validate()) return
  submitting.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    bookStore.reset()
    toast.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.replace(redirect)
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '登录失败，请稍后再试'
    toast.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <aside class="login-side">
      <div class="side-texture" aria-hidden="true"></div>
      <div class="mountains" aria-hidden="true">
        <svg viewBox="0 0 600 280" preserveAspectRatio="none" class="mountain-svg">
          <defs>
            <linearGradient id="mist" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--c-on-nav)" stop-opacity="0" />
              <stop offset="50%" stop-color="var(--c-on-nav)" stop-opacity="0.45" />
              <stop offset="100%" stop-color="var(--c-on-nav)" stop-opacity="0" />
            </linearGradient>
            <radialGradient id="sunHalo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="var(--c-seal)" stop-opacity="0.5" />
              <stop offset="100%" stop-color="var(--c-seal)" stop-opacity="0" />
            </radialGradient>
            <!-- 提升山体不透明度，让山水图形在深棕底上更清晰可辨 -->
            <linearGradient id="mFar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--c-on-nav)" stop-opacity="0.10" />
              <stop offset="100%" stop-color="var(--c-on-nav)" stop-opacity="0.20" />
            </linearGradient>
            <linearGradient id="mMid" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--c-on-nav)" stop-opacity="0.16" />
              <stop offset="100%" stop-color="var(--c-on-nav)" stop-opacity="0.30" />
            </linearGradient>
            <linearGradient id="mNear" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--c-on-nav)" stop-opacity="0.22" />
              <stop offset="100%" stop-color="var(--c-on-nav)" stop-opacity="0.40" />
            </linearGradient>
          </defs>

          <!-- 红日（衔山，带高光） -->
          <circle cx="424" cy="100" r="48" fill="url(#sunHalo)" />
          <circle cx="424" cy="100" r="17" fill="var(--c-seal)" opacity="0.95" />
          <circle cx="420" cy="96" r="7" fill="#e6b8aa" opacity="0.45" />

          <!-- 飞鸟 -->
          <path
            d="M348 92 q6 -7 12 0 M366 82 q6 -6 11 0"
            stroke="oklch(0.945 0.012 85 / 0.7)"
            stroke-width="1.5"
            fill="none"
            stroke-linecap="round"
          />

          <!-- 远山（最淡，水墨渐变） -->
          <path
            d="M0 206 L56 158 L104 186 L172 132 L232 170 L300 142 L356 180 L428 118 L496 170 L558 150 L600 178 L600 250 L0 250 Z"
            fill="url(#mFar)"
          />
          <ellipse cx="300" cy="196" rx="370" ry="10" fill="url(#mist)" />

          <!-- 中景山 -->
          <path
            d="M0 232 L72 182 L148 216 L230 172 L310 212 L390 180 L470 214 L548 186 L600 214 L600 258 L0 258 Z"
            fill="url(#mMid)"
          />
          <ellipse cx="340" cy="228" rx="350" ry="8" fill="url(#mist)" />

          <!-- 近山（最浓） -->
          <path
            d="M0 252 L92 218 L176 246 L270 210 L360 244 L452 218 L538 246 L600 226 L600 264 L0 264 Z"
            fill="url(#mNear)"
          />

          <!-- 水 -->
          <rect x="0" y="258" width="600" height="22" fill="oklch(0.945 0.012 85 / 0.1)" />

          <!-- 孤舟 -->
          <path
            d="M118 268 q20 -5 42 0 q-4 5 -21 5 q-18 0 -21 -5 z"
            fill="oklch(0.945 0.012 85 / 0.65)"
          />
          <path d="M139 268 l0 -14 l11 6 z" fill="oklch(0.945 0.012 85 / 0.55)" />

          <!-- 水纹 -->
          <path
            d="M64 274 q10 -4 20 0 M170 275 q9 -3 18 0 M230 272 q8 -3 16 0"
            stroke="oklch(0.945 0.012 85 / 0.5)"
            stroke-width="1.3"
            fill="none"
            stroke-linecap="round"
          />
        </svg>
      </div>
      <div class="side-inner">
        <div class="brand">
          <span class="seal" aria-hidden="true">记</span>
          <span class="brand-name">个人记账</span>
        </div>

        <div class="side-statement">
          <p class="statement-line">每一笔，都算数。</p>
          <p class="statement-sub">流水不争先，争的是滔滔不绝。</p>
          <p class="side-dateline">丙午 · 八月 立秋后 第拾贰日</p>
        </div>
      </div>

      <span class="vertical-text" aria-hidden="true">家财万贯 · 不如日进斗金</span>
    </aside>

    <main class="login-main">
      <div class="form-card">
        <h1 class="form-title">欢迎回来</h1>
        <p class="form-sub">砚墨已备，执笔入账。</p>

        <form novalidate @submit.prevent="onSubmit">
          <div class="field">
            <label class="field-label" for="username">用户名</label>
            <input
              id="username"
              v-model="form.username"
              class="input"
              :class="{ 'input--invalid': usernameError }"
              autocomplete="username"
              placeholder="请输入用户名"
              @input="usernameError = ''"
            />
            <span v-if="usernameError" class="field-error">{{ usernameError }}</span>
          </div>

          <div class="field">
            <label class="field-label" for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="input"
              :class="{ 'input--invalid': passwordError }"
              autocomplete="current-password"
              placeholder="请输入密码"
              @input="passwordError = ''"
            />
            <span v-if="passwordError" class="field-error">{{ passwordError }}</span>
          </div>

          <button type="submit" class="btn btn--primary submit-btn" :disabled="submitting">
            <span v-if="submitting" class="spinner" aria-hidden="true"></span>
            {{ submitting ? '登录中…' : '登录' }}
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: var(--c-bg);
}

/* ---------- 左栏：暖棕 + 编辑排版 ---------- */
.login-side {
  position: relative;
  flex: 1 1 44%;
  max-width: 560px;
  background: var(--c-nav-bg);
  color: var(--c-on-nav);
  overflow: hidden;
  display: flex;
  align-items: stretch;
}

.side-texture {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: repeating-linear-gradient(
    180deg,
    transparent,
    transparent 22px,
    oklch(0.9 0.02 80 / 0.06) 22px,
    oklch(0.9 0.02 80 / 0.06) 23px
  );
}

.mountains {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 280px;
  pointer-events: none;
  z-index: 0;
  animation: rise 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.35s both;
}

.mountains svg {
  width: 100%;
  height: 100%;
  display: block;
}

.side-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  padding: 44px 40px;
  width: 100%;
}

.brand {
  animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.statement-line {
  animation: rise 0.55s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
}

.statement-sub {
  animation: rise 0.55s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
}

.side-dateline {
  animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.45s both;
}

.brand {
  display: flex;
  align-items: center;
  gap: 13px;
}

.brand-name {
  font-family: var(--font-kai);
  font-size: 22px;
  letter-spacing: 0.14em;
  color: var(--c-on-nav);
}

.side-statement {
  margin: auto 0;
}

.side-dateline {
  margin-top: 26px;
  font-family: var(--font-display);
  font-size: 12px;
  letter-spacing: 0.18em;
  color: var(--c-nav-muted);
}

.vertical-text {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  font-family: var(--font-display);
  letter-spacing: 0.3em;
  font-size: 12px;
  color: oklch(0.9 0.02 80 / 0.45);
  pointer-events: none;
  z-index: 1;
  animation: fade-in 0.8s ease 0.65s both;
}

.statement-line {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 5vw, 2.5rem);
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: 0.02em;
}

.statement-sub {
  margin-top: 20px;
  max-width: 340px;
  color: var(--c-nav-text);
  font-family: var(--font-display);
  font-size: 17px;
  letter-spacing: 0.04em;
  line-height: 1.8;
}

/* ---------- 右栏：暖纸表单 ---------- */
.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.form-card {
  width: 100%;
  max-width: 440px;
}

.form-title {
  position: relative;
  font-family: var(--font-kai);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.12em;
  padding-bottom: 16px;
}

/* 题名双线：左端琥珀粗短线 + 全宽细线 */
.form-title::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -3px;
  height: 1px;
  background: var(--c-border-strong);
}

.form-title::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 36px;
  height: 3px;
  background: var(--c-primary);
}

.form-sub {
  margin: 12px 0 32px;
  color: var(--c-text-secondary);
  font-family: var(--font-kai);
  font-size: 15px;
  letter-spacing: 0.1em;
}

.form-card form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}

.spinner {
  width: 15px;
  height: 15px;
  border: 2px solid oklch(0.985 0.005 85 / 0.4);
  border-top-color: var(--c-on-primary);
  border-radius: 9999px;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1024px) {
  .login-page {
    flex-direction: column;
  }

  .login-side {
    max-width: none;
    flex: none;
    min-height: 300px;
    padding: 28px 24px 36px;
  }

  .mountains {
    height: 150px;
  }

  .side-inner {
    padding: 0;
  }

  .side-statement {
    margin-top: 36px;
    padding-bottom: 0;
  }
}
</style>
