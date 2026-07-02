<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { saveTokens, isAuthenticated } from '@/auth.js'

const router = useRouter()

// Если уже авторизован — сразу на главную
onMounted(() => {
  if (isAuthenticated()) {
    router.replace('/')
  }
})

const mode = ref('login') // 'login' | 'register'
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const canRegister = ref(false)

async function checkCanRegister() {
  try {
    const res = await axios.get('/api/can_register')
    canRegister.value = res.data?.can_register === true
  } catch {
    canRegister.value = false
  }
}

onMounted(checkCanRegister)

function switchMode(newMode) {
  mode.value = newMode
  error.value = ''
}

async function submit() {
  error.value = ''

  if (!email.value.trim() || !password.value) {
    error.value = 'Заполните email и пароль'
    return
  }
  if (password.value.length < 4) {
    error.value = 'Пароль должен быть минимум 4 символа'
    return
  }

  loading.value = true
  try {
    const endpoint = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const res = await axios.post(endpoint, {
      email: email.value.trim(),
      password: password.value
    })
    saveTokens(res.data.access_token, res.data.refresh_token)
    window.dispatchEvent(new Event('auth-changed'))
    router.replace('/')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (detail) {
      error.value = detail
    } else if (e.response?.status === 401) {
      error.value = 'Неверный email или пароль'
    } else if (e.response?.status === 400) {
      error.value = 'Email уже зарегистрирован'
    } else {
      error.value = 'Ошибка соединения с сервером'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card glass">
      <!-- Заголовок -->
      <div class="login-head">
        <svg class="login-icon" width="40" height="40" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
             stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <h1 class="login-title">Семейное древо</h1>
        <p class="login-sub">
          {{ mode === 'login' ? 'Войдите в свою учётную запись' : 'Создайте новую учётную запись' }}
        </p>
      </div>

      <!-- Переключатель -->
      <div class="mode-tabs">
        <button
          class="mode-tab"
          :class="{ active: mode === 'login' }"
          @click="switchMode('login')"
        >Вход</button>
        <button
          v-if="canRegister"
          class="mode-tab"
          :class="{ active: mode === 'register' }"
          @click="switchMode('register')"
        >Регистрация</button>
      </div>

      <!-- Форма -->
      <form class="login-form" @submit.prevent="submit">
        <div class="field">
          <label class="field-label" for="email">Email</label>
          <input
            id="email"
            v-model="email"
            class="field-input"
            type="email"
            placeholder="example@mail.com"
            autocomplete="email"
            @input="error = ''"
          />
        </div>

        <div class="field">
          <label class="field-label" for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            class="field-input"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            @input="error = ''"
          />
        </div>

        <!-- Ошибка -->
        <div v-if="error" class="error-msg">{{ error }}</div>

        <!-- Кнопка -->
        <button
          class="btn-submit"
          type="submit"
          :disabled="loading"
        >
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>{{ mode === 'login' ? 'Войти' : 'Зарегистрироваться' }}</span>
        </button>
      </form>

      <!-- Ссылка переключения -->
      <p v-if="canRegister" class="switch-hint">
        <template v-if="mode === 'login'">
          Нет аккаунта?
          <button class="link-btn" @click="switchMode('register')">Зарегистрироваться</button>
        </template>
        <template v-else>
          Уже есть аккаунт?
          <button class="link-btn" @click="switchMode('login')">Войти</button>
        </template>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 36px 32px;
  border-radius: var(--r-lg);
  box-shadow: var(--sh-card);
}

/* ─── Заголовок ─── */
.login-head {
  text-align: center;
  margin-bottom: 28px;
}
.login-icon {
  color: var(--tint);
  margin-bottom: 12px;
}
.login-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}
.login-sub {
  font-size: 14px;
  color: var(--ink-3);
}

/* ─── Переключатель ─── */
.mode-tabs {
  display: flex;
  background: var(--glass-thin);
  border-radius: var(--r-pill);
  padding: 3px;
  margin-bottom: 24px;
}
.mode-tab {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--ink-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s var(--ease-out);
  font-family: inherit;
}
.mode-tab.active {
  background: var(--tint);
  color: #fff;
  box-shadow: var(--sh-soft);
}
.mode-tab:not(.active):hover {
  color: var(--ink);
}

/* ─── Поля формы ─── */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.field-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--r-pill);
  border: 1px solid var(--hairline);
  background: var(--glass-thin);
  color: var(--ink);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s var(--ease-out), box-shadow .15s var(--ease-out);
  box-sizing: border-box;
}
.field-input:focus {
  border-color: var(--tint);
  box-shadow: 0 0 0 3px var(--tint-tr);
}
.field-input::placeholder {
  color: var(--ink-4);
}

/* ─── Ошибка ─── */
.error-msg {
  font-size: 13px;
  font-weight: 500;
  color: #D94A6B;
  background: rgba(217, 74, 107, 0.1);
  padding: 10px 14px;
  border-radius: var(--r-sm);
  text-align: center;
}

/* ─── Кнопка ─── */
.btn-submit {
  width: 100%;
  padding: 11px 20px;
  border-radius: var(--r-pill);
  border: none;
  background: var(--tint);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background .15s var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-submit:hover:not(:disabled) {
  background: var(--tint-2);
}
.btn-submit:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ─── Переключение ─── */
.switch-hint {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: var(--ink-3);
}
.link-btn {
  background: none;
  border: none;
  color: var(--tint);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.link-btn:hover {
  color: var(--tint-2);
}
</style>
