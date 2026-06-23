<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import EventTableRow from '@/components/EventTableRow.vue'

const events = ref([])
const loading = ref(true)
const error = ref(null)
const filterType = ref('all')

/** Все уникальные типы событий для фильтра */
const eventTypes = computed(() => {
  const types = new Set(events.value.map(e => e.type))
  return ['all', ...types]
})

/** Отфильтрованные события */
const filteredEvents = computed(() => {
  if (filterType.value === 'all') return events.value
  return events.value.filter(e => e.type === filterType.value)
})

async function fetchEvents() {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get('/api/events')
    events.value = res.data
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchEvents)
</script>

<template>
  <div class="events-page">
    <!-- Заголовок -->
    <div class="page-head">
      <h1 class="page-title">Хронология событий</h1>
      <p class="page-sub">Всего событий: <strong>{{ events.length }}</strong></p>
    </div>

    <!-- Фильтр по типу -->
    <div class="filter-bar glass">
      <span class="filter-label">Тип события:</span>
      <div class="filter-chips">
        <button
          v-for="type in eventTypes"
          :key="type"
          class="chip"
          :class="{ active: filterType === type }"
          @click="filterType = type"
        >
          {{ type === 'all' ? 'Все' : type }}
          <span v-if="type !== 'all'" class="chip-count">
            {{ events.filter(e => e.type === type).length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Состояния -->
    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Загрузка событий…</span>
    </div>
    <div v-else-if="error" class="state-msg error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchEvents">Повторить</button>
    </div>

    <!-- Таблица -->
    <div v-else class="table-wrap glass">
      <table class="events-table">
        <thead>
          <tr>
            <th class="th-type">Событие</th>
            <th class="th-person">Имя</th>
            <th class="th-date">Дата</th>
            <th class="th-desc">Описание</th>
            <th class="th-place">Место</th>
          </tr>
        </thead>
        <tbody>
          <EventTableRow
            v-for="ev in filteredEvents"
            :key="ev.id"
            :event="ev"
          />
          <tr v-if="filteredEvents.length === 0">
            <td colspan="4" class="empty-row">Нет событий</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.events-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* ─── Заголовок ─── */
.page-head {
  margin-bottom: 24px;
}
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}
.page-sub {
  font-size: 14px;
  color: var(--ink-3);
}

/* ─── Фильтр ─── */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--r-md);
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  white-space: nowrap;
}
.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chip {
  padding: 5px 12px;
  border-radius: var(--r-pill);
  border: 1px solid var(--hairline);
  background: transparent;
  color: var(--ink-2);
  font-size: 12px;
  cursor: pointer;
  transition: all .15s var(--ease-out);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}
.chip:hover {
  background: var(--glass-thin);
  color: var(--ink);
}
.chip.active {
  background: var(--tint);
  border-color: var(--tint);
  color: #fff;
}
.chip-count {
  font-size: 10px;
  opacity: .7;
}
.chip.active .chip-count {
  opacity: .85;
}

/* ─── Состояния ─── */
.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 80px 0;
  color: var(--ink-2);
  font-size: 15px;
}
.state-msg.error {
  color: #D94A6B;
}
.spinner {
  width: 32px;
  height: 32px;
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

/* ─── Таблица ─── */
.table-wrap {
  border-radius: var(--r-lg);
  overflow: hidden;
}
.events-table {
  width: 100%;
  border-collapse: collapse;
}
.events-table thead th {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--ink-3);
  text-align: left;
  border-bottom: 1px solid var(--hairline);
  background: var(--glass-thin);
}
.th-type { width: 130px; }
.th-date { width: 120px; }
.th-desc { /* auto */ }
.th-place { width: 200px; }

.empty-row {
  text-align: center;
  padding: 40px 16px !important;
  color: var(--ink-4);
  font-size: 14px;
}
</style>
