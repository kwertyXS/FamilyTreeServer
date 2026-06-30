<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import malePlaceholder from '../components/placeholder-male.svg'
import femalePlaceholder from '../components/placeholder-female.svg'

const route = useRoute()
const router = useRouter()

const person = ref(null)
const allPersons = ref([])
const loading = ref(true)
const error = ref(null)

const personId = computed(() => route.params.id)

const sexLabel = computed(() => {
  if (person.value?.sex === true) return '♂ Мужской'
  if (person.value?.sex === false) return '♀ Женский'
  return null
})

const placeholderSrc = computed(() => {
  return person.value?.sex === true ? malePlaceholder : femalePlaceholder
})

const relationNameMap = computed(() => {
  const map = {}
  for (const p of allPersons.value) {
    map[p.id] = p.full_name
  }
  return map
})

async function fetchPerson() {
  loading.value = true
  error.value = null
  try {
    const [personRes, allRes] = await Promise.all([
      axios.get(`/api/persons/${personId.value}`),
      axios.get('/api/persons'),
    ])
    person.value = personRes.data
    allPersons.value = allRes.data
  } catch (e) {
    error.value = e.message || 'Не удалось загрузить данные'
  } finally {
    loading.value = false
  }
}

onMounted(fetchPerson)

watch(() => route.params.id, () => {
  fetchPerson()
  window.scrollTo({ top: 0, behavior: 'smooth' })
})
</script>

<template>
  <div class="person-page">
    <!-- Шапка с навигацией -->
    <header class="page-header glass">
      <button class="back-btn" @click="router.back()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"/>
          <path d="M12 19l-7-7 7-7"/>
        </svg>
        Назад
      </button>
    </header>

    <!-- Загрузка -->
    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Загрузка…</span>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="state-msg error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchPerson">Повторить</button>
    </div>

    <!-- Основной контент -->
    <div v-else-if="person" class="person-content">

      <!-- HERO -->
      <section class="hero glass">
        <div class="hero-photo-wrap">
          <img
            v-if="person.photo"
            :src="'/photos/' + person.photo"
            :alt="person.full_name"
            class="hero-photo"
          />
          <img
            v-else
            :src="placeholderSrc"
            :alt="person.full_name"
            class="hero-photo"
          />
          <span v-if="person.is_favorite" class="hero-fav">★</span>
        </div>

        <div class="hero-info">
          <h1 class="hero-name">{{ person.full_name }}</h1>
          <div v-if="person.family_name" class="hero-family">{{ person.family_name }}</div>
          <div class="hero-dates">
            <span>{{ person.birth_date || '…' }}</span>
            <span class="hero-dates-sep">—</span>
            <span>{{ person.death_date || '…' }}</span>
            <span v-if="person.lifespan" class="hero-lifespan">· {{ person.lifespan }}</span>
          </div>
          <div v-if="person.occupation" class="hero-occupation">{{ person.occupation }}</div>
          <div v-if="person.maiden_surname" class="hero-maiden">
            <span class="hero-maiden-label">Девичья фамилия:</span>
            {{ person.maiden_surname }}
          </div>
        </div>
      </section>

      <div class="person-grid">

        <!-- Основная информация -->
        <section class="card glass">
          <h2 class="card-title">Основная информация</h2>
          <dl class="info-list">
            <div class="info-row">
              <dt>Имя</dt>
              <dd>{{ person.first_name || '—' }}</dd>
            </div>
            <div class="info-row">
              <dt>Фамилия</dt>
              <dd>{{ person.surname || '—' }}</dd>
            </div>
            <div class="info-row">
              <dt>Отчество</dt>
              <dd>{{ person.middle_name || '—' }}</dd>
            </div>
            <div class="info-row" v-if="person.maiden_surname">
              <dt>Девичья фамилия</dt>
              <dd>{{ person.maiden_surname }}</dd>
            </div>
            <div class="info-row">
              <dt>Пол</dt>
              <dd>{{ sexLabel || '—' }}</dd>
            </div>
            <div class="info-row" v-if="person.family_name">
              <dt>Семья</dt>
              <dd>{{ person.family_name }}</dd>
            </div>
            <div class="info-row" v-if="person.occupation">
              <dt>Профессия</dt>
              <dd>{{ person.occupation }}</dd>
            </div>
            <div class="info-row">
              <dt>Дата рождения</dt>
              <dd>{{ person.birth_date || '—' }}</dd>
            </div>
            <div class="info-row">
              <dt>Дата смерти</dt>
              <dd>{{ person.death_date || '—' }}</dd>
            </div>
            <div class="info-row" v-if="person.lifespan">
              <dt>Продолжительность жизни</dt>
              <dd>{{ person.lifespan }}</dd>
            </div>
            <div class="info-row" v-if="person.death_reason">
              <dt>Причина смерти</dt>
              <dd>{{ person.death_reason }}</dd>
            </div>
          </dl>
        </section>

        <!-- Биография -->
        <section v-if="person.biography" class="card glass card--wide">
          <h2 class="card-title">Биография</h2>
          <div class="bio-text">{{ person.biography }}</div>
        </section>

        <!-- Места -->
        <section v-if="person.birth_place || person.death_place || person.place" class="card glass">
          <h2 class="card-title">Места</h2>
          <div class="places-list">
            <div v-if="person.birth_place" class="place-row">
              <span class="place-icon">🏠</span>
              <span class="place-label">Родился</span>
              <span class="place-name">{{ person.birth_place.full_name }}</span>
            </div>
            <div v-if="person.death_place" class="place-row">
              <span class="place-icon">⚰️</span>
              <span class="place-label">Умер</span>
              <span class="place-name">{{ person.death_place.full_name }}</span>
            </div>
            <div v-if="person.place" class="place-row">
              <span class="place-icon">📍</span>
              <span class="place-label">Проживает</span>
              <span class="place-name">{{ person.place.full_name }}</span>
            </div>
          </div>
        </section>

        <!-- События -->
        <section v-if="person.events && person.events.length > 0" class="card glass card--wide">
          <h2 class="card-title">События жизни</h2>
          <div class="events-timeline">
            <div v-for="ev in person.events" :key="ev.id" class="event-item">
              <div class="event-marker">
                <div class="event-dot"></div>
                <div class="event-line"></div>
              </div>
              <div class="event-body">
                <div class="event-head">
                  <span v-if="ev.date" class="event-date">{{ ev.date }}</span>
                  <span class="event-type">{{ ev.type }}</span>
                </div>
                <div v-if="ev.description" class="event-desc">{{ ev.description }}</div>
                <div v-if="ev.place" class="event-place">{{ ev.place.full_name }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- Родственники -->
        <section v-if="person.relations && person.relations.length > 0" class="card glass">
          <h2 class="card-title">Семья</h2>
          <div class="relations-list">
            <div
              v-for="(rel, idx) in person.relations"
              :key="idx"
              class="relation-row"
              @click="router.push('/person/' + rel.related_person_id)"
            >
              <span class="relation-icon">👤</span>
              <span class="relation-label">{{ rel.relation_label }}</span>
              <span class="relation-arrow">→</span>
              <span class="relation-name">{{ relationNameMap[rel.related_person_id] || rel.related_person_id }}</span>
            </div>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
.person-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 24px 80px;
}

/* ─── Шапка ─── */
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: var(--r-md);
  margin-bottom: 24px;
}
.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--ink-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: background .15s var(--ease-out), color .15s var(--ease-out);
}
.back-btn:hover {
  background: var(--glass-thick);
  color: var(--ink);
}

/* ─── Состояния ─── */
.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 120px 0;
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

/* ─── Hero ─── */
.hero {
  display: flex;
  gap: 28px;
  padding: 28px;
  border-radius: var(--r-lg);
  margin-bottom: 24px;
}
.hero-photo-wrap {
  position: relative;
  flex-shrink: 0;
  width: 160px;
  height: 160px;
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--bg-1);
}
.hero-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hero-fav {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 20px;
  color: #F5A623;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.25));
  line-height: 1;
}
.hero-sex-badge {
  position: absolute;
  bottom: 6px;
  left: 6px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background: var(--glass-thick);
  backdrop-filter: blur(8px);
  border: 1px solid var(--edge-hi);
  line-height: 1;
}
.hero-sex-badge.male   { color: #3A6BD9; }
.hero-sex-badge.female { color: #D94A6B; }

.hero-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 0;
}
.hero-name {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.2;
}
.hero-family {
  font-size: 15px;
  color: var(--ink-3);
}
.hero-dates {
  font-size: 15px;
  color: var(--ink-2);
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.hero-dates-sep { color: var(--ink-4); }
.hero-lifespan { color: var(--ink-3); font-size: 13px; }
.hero-occupation {
  font-size: 14px;
  color: var(--tint);
  margin-top: 4px;
}
.hero-maiden {
  font-size: 13px;
  color: var(--ink-3);
  margin-top: 2px;
}
.hero-maiden-label {
  color: var(--ink-4);
}

/* ─── Сетка карточек ─── */
.person-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  padding: 24px;
  border-radius: var(--r-md);
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--hairline);
}

/* ─── Информация (definition list) ─── */
.info-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.info-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid var(--hairline-soft);
}
.info-row:last-child { border-bottom: none; }
.info-row dt {
  flex: 0 0 180px;
  font-size: 13px;
  color: var(--ink-3);
  font-weight: 400;
}
.info-row dd {
  flex: 1;
  font-size: 14px;
  color: var(--ink);
  font-weight: 450;
}

/* ─── Биография ─── */
.bio-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink-2);
  white-space: pre-wrap;
}

/* ─── Места ─── */
.places-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.place-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.place-icon { flex-shrink: 0; font-size: 16px; }
.place-label {
  flex-shrink: 0;
  color: var(--ink-3);
  font-size: 13px;
  width: 70px;
}
.place-name {
  color: var(--ink);
  font-weight: 450;
}

/* ─── События (таймлайн) ─── */
.events-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.event-item {
  display: flex;
  gap: 16px;
  position: relative;
}
.event-item:last-child .event-line { display: none; }

.event-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
  padding-top: 4px;
}
.event-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--tint);
  flex-shrink: 0;
  z-index: 1;
}
.event-line {
  width: 2px;
  flex: 1;
  background: var(--hairline);
  min-height: 20px;
}

.event-body {
  flex: 1;
  padding-bottom: 20px;
  min-width: 0;
}
.event-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}
.event-date {
  font-size: 13px;
  color: var(--ink-3);
  white-space: nowrap;
}
.event-type {
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
}
.event-desc {
  margin-top: 4px;
  font-size: 13px;
  color: var(--ink-2);
  line-height: 1.5;
}
.event-place {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ink-3);
}

/* ─── Родственники ─── */
.relations-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.relation-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: background .15s var(--ease-out);
}
.relation-row:hover {
  background: var(--glass-thick);
}
.relation-icon { flex-shrink: 0; font-size: 16px; }
.relation-label {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--ink-3);
  width: 80px;
}
.relation-arrow {
  color: var(--ink-4);
  font-size: 13px;
  flex-shrink: 0;
}
.relation-name {
  font-size: 14px;
  color: var(--tint);
  font-weight: 500;
}

/* ─── Адаптивность ─── */
@media (max-width: 600px) {
  .hero {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 16px;
    padding: 20px;
  }
  .hero-photo-wrap {
    width: 120px;
    height: 120px;
  }
  .hero-info { align-items: center; }
  .hero-dates { justify-content: center; }
  .hero-name { font-size: 22px; }
  .info-row { flex-direction: column; gap: 2px; }
  .info-row dt { flex: none; }
}
</style>
