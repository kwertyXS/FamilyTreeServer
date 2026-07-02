<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isAuthenticated, isAdmin, clearTokens } from '@/auth.js'

const router = useRouter()
const route = useRoute()

const isAuth = ref(false)
const isAdminUser = ref(false)

function updateAll() {
  isAuth.value = isAuthenticated()
  isAdminUser.value = isAdmin()
}

onMounted(() => {
  updateAll()
  window.addEventListener('auth-changed', updateAll)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', updateAll)
})

function logout() {
  clearTokens()
  updateAll()
  router.push('/login')
}

const allNavItems = [
  { path: '/',        label: 'Древо',   icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5' },
  { path: '/persons', label: 'Люди',    icon: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-4 0-6 2-6 4v1h12v-1c0-2-2-4-6-4z' },
  { path: '/events',  label: 'События', icon: 'M8 2v4M16 2v4M3 9h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 6v8m4-8v8m4-8v8m4-8v8' },
  { path: '/admin',   label: 'Админ',   icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm0 0v5m-8-8a8 8 0 1 1 16 0' },
]
</script>

<template>
  <!-- Ambient blobs -->
  <div class="ambient" aria-hidden="true">
    <div class="blob b1"></div>
    <div class="blob b2"></div>
    <div class="blob b3"></div>
  </div>

  <!-- Vignette -->
  <div class="vignette" aria-hidden="true"></div>

  <!-- Навигация (только для авторизованных) -->
  <nav v-if="isAuth" class="topnav glass">
    <template v-for="item in allNavItems" :key="item.path">
      <router-link
        v-if="item.path !== '/admin' || isAdminUser"
        :to="item.path"
        class="nav-link"
        :class="{ active: route.path === item.path }"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
             stroke-linejoin="round">
          <path :d="item.icon"/>
        </svg>
        <span>{{ item.label }}</span>
      </router-link>
    </template>

    <div class="nav-sep"></div>

    <button class="nav-link logout-btn" @click="logout" title="Выйти">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
           stroke-linejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14l5-5-5-5m5 5H9"/>
      </svg>
      <span>Выйти</span>
    </button>
  </nav>

  <!-- Основной контент -->
  <main class="main-content">
    <router-view />
  </main>
</template>

<style scoped>
/* ─── Навигация ─── */
.topnav {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  padding: 5px;
  border-radius: var(--r-pill);
  z-index: 100;
  box-shadow: var(--sh-card);
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--r-pill);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  transition: all .2s var(--ease-out);
  white-space: nowrap;
}
.nav-link:hover {
  color: var(--ink);
  background: var(--glass-thick);
}
.nav-link.active {
  color: #fff;
  background: var(--tint);
}

/* ─── Разделитель ─── */
.nav-sep {
  width: 1px;
  height: 24px;
  background: var(--hairline);
  margin: auto 4px;
}

/* ─── Кнопка выхода ─── */
.logout-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}
.logout-btn:hover {
  color: #D94A6B;
}

/* ─── Контент ─── */
.main-content {
  position: relative;
  z-index: 1;
}
</style>
