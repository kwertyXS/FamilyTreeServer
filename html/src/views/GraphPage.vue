<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import GraphCard from '@/components/GraphCard.vue'

const persons = ref([])
const edges = ref([])
const loading = ref(true)
const error = ref(null)

async function fetchTree() {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get('/api/tree')
    persons.value = res.data.persons
    edges.value = res.data.edges
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchTree)
</script>

<template>
  <div class="graph-page">
    <!-- Заголовок -->
    <div class="page-head">
      <h1 class="page-title">Семейное древо</h1>
      <p class="page-sub">Всего человек: <strong>{{ persons.length }}</strong>, связей: <strong>{{ edges.length }}</strong></p>
    </div>

    <!-- Состояния загрузки / ошибки -->
    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Загрузка дерева…</span>
    </div>
    <div v-else-if="error" class="state-msg error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchTree">Повторить</button>
    </div>

    <!-- Сетка карточек -->
    <div v-else class="graph-grid">
      <GraphCard
        v-for="person in persons"
        :key="person.id"
        :person="person"
      />
    </div>
  </div>
</template>

<style scoped>
.graph-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* ─── Заголовок ─── */
.page-head {
  margin-bottom: 32px;
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

/* ─── Загрузка / Ошибка ─── */
.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
  transition: background .15s var(--ease-out);
}
.retry-btn:hover {
  background: var(--glass-thick);
}

/* ─── Сетка ─── */
.graph-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}
</style>
