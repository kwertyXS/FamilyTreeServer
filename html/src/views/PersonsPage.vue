<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const persons = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')

const filteredPersons = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return persons.value

  return persons.value.filter(p => {
    const fields = [
      p.full_name,
      p.family_name,
      p.birth_date,
      p.death_date,
      p.lifespan,
      p.sex != null ? (p.sex ? 'мужской' : 'женский') : '',
      p.is_favorite ? 'избранный' : '',
      p.birth_place,
      p.death_place,
    ]
    return fields.some(f => f && String(f).toLowerCase().includes(q))
  })
})

async function fetchPersons() {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get('/api/persons')
    persons.value = res.data
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchPersons)
</script>

<template>
  <div class="persons-page">
    <div class="page-head">
      <h1 class="page-title">Список людей</h1>
      <p class="page-sub">Всего человек: <strong>{{ persons.length }}</strong></p>
    </div>

    <!-- Поиск -->
    <div class="search-bar glass">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="Поиск по имени, датам, месту рождения/смерти…"
      />
      <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''" title="Очистить">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Загрузка…</span>
    </div>
    <div v-else-if="error" class="state-msg error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchPersons">Повторить</button>
    </div>

    <div v-else class="persons-grid">
      <div
        v-for="person in filteredPersons"
        :key="person.id"
        class="person-card glass"
        @click="$router.push('/person/' + person.id)"
      >
        <!-- Фото -->
        <div class="photo-wrap">
          <img
            v-if="person.photo"
            :src="'/photos/' + person.photo"
            :alt="person.full_name"
            class="photo"
          />
          <div v-else class="photo-placeholder">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <span v-if="person.sex != null" class="sex-badge" :class="person.sex ? 'male' : 'female'">
            {{ person.sex ? '♂' : '♀' }}
          </span>
          <span v-if="person.is_favorite" class="fav-badge">★</span>
        </div>

        <!-- Инфо -->
        <div class="info">
          <div class="name">{{ person.full_name }}</div>
          <div v-if="person.family_name" class="family">{{ person.family_name }}</div>
          <div class="dates">
            <span>{{ person.birth_date || '…' }}</span>
            <span class="sep">—</span>
            <span>{{ person.death_date || '…' }}</span>
          </div>
          <div v-if="person.lifespan" class="lifespan">{{ person.lifespan }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.persons-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

.page-head { margin-bottom: 32px; }
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}
.page-sub { font-size: 14px; color: var(--ink-3); }

/* ─── Поиск ─── */
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: var(--r-md);
  margin-bottom: 24px;
}
.search-icon {
  flex-shrink: 0;
  color: var(--ink-3);
}
.search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: var(--ink);
  font-family: inherit;
}
.search-input::placeholder {
  color: var(--ink-4);
}
.search-clear {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--ink-3);
  cursor: pointer;
  transition: background .15s var(--ease-out);
}
.search-clear:hover {
  background: var(--glass-thick);
  color: var(--ink);
}

.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 80px 0;
  color: var(--ink-2);
  font-size: 15px;
}
.state-msg.error { color: #D94A6B; }
.spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--hairline);
  border-top-color: var(--tint);
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.retry-btn {
  padding: 8px 20px;
  border-radius: var(--r-pill);
  border: 1px solid var(--hairline);
  background: var(--glass-regular);
  color: var(--ink);
  font-size: 13px;
  cursor: pointer;
}
.retry-btn:hover { background: var(--glass-thick); }

/* ─── Сетка ─── */
.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 20px;
}

/* ─── Карточка ─── */
.person-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: var(--r-md);
  cursor: pointer;
  transition: transform .2s var(--ease-out), box-shadow .2s var(--ease-out);
}
.person-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--sh-lift);
}

.photo-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: var(--r-sm);
  overflow: hidden;
  background: var(--bg-1);
}
.photo {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
}
.photo-placeholder {
  width: 100%; height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
}

.sex-badge {
  position: absolute;
  bottom: 6px; left: 6px;
  width: 24px; height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  background: var(--glass-thick);
  backdrop-filter: blur(8px);
  border: 1px solid var(--edge-hi);
}
.sex-badge.male   { color: #3A6BD9; }
.sex-badge.female { color: #D94A6B; }

.fav-badge {
  position: absolute;
  top: 6px; right: 6px;
  color: #F5A623;
  font-size: 18px;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.25));
}

.info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.name { font-weight: 600; font-size: 14px; line-height: 1.3; color: var(--ink); }
.family { font-size: 12px; color: var(--ink-3); }
.dates {
  font-size: 12px;
  color: var(--ink-2);
  display: flex;
  gap: 4px;
}
.sep { color: var(--ink-4); }
.lifespan { font-size: 11px; color: var(--ink-3); }
</style>
