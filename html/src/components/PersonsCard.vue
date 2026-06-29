<script setup>
defineProps({
  person: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <div class="graph-card glass">
    <!-- Фото -->
    <div class="photo-wrap">
      <img
        v-if="person.photo"
        :src="'/photos/' + person.photo"
        :alt="person.full_name"
        class="photo"
      />
      <div v-else class="photo-placeholder">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <!-- Пол -->
      <span v-if="person.sex" class="sex-badge" :class="person.sex === 'М' ? 'male' : 'female'">
        {{ person.sex === 'М' ? '♂' : '♀' }}
      </span>
      <!-- Избранное -->
      <span v-if="person.is_favorite" class="fav-badge" title="Избранный">★</span>
    </div>

    <!-- Инфо -->
    <div class="info">
      <div class="name">{{ person.full_name }}</div>
      <div v-if="person.family_name" class="family">{{ person.family_name }}</div>
      <div class="dates">
        <template v-if="person.birth_date || person.death_date">
          <span class="date">{{ person.birth_date || '…' }}</span>
          <span class="sep">—</span>
          <span class="date">{{ person.death_date || '…' }}</span>
        </template>
        <span v-else class="no-dates">Нет данных</span>
      </div>
      <div v-if="person.lifespan" class="lifespan">{{ person.lifespan }}</div>
    </div>
  </div>
</template>

<style scoped>
.graph-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: var(--r-md);
  width: 200px;
  transition: transform .2s var(--ease-out), box-shadow .2s var(--ease-out);
  cursor: default;
}
.graph-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--sh-lift);
}

/* ─── Фото ─── */
.photo-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: var(--r-sm);
  overflow: hidden;
  background: var(--bg-1);
}
.photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.photo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
}

.sex-badge {
  position: absolute;
  bottom: 6px;
  left: 6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  background: var(--glass-thick);
  backdrop-filter: blur(8px);
  border: 1px solid var(--edge-hi);
}
.sex-badge.male  { color: #3A6BD9; }
.sex-badge.female{ color: #D94A6B; }

.fav-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  color: #F5A623;
  font-size: 18px;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.25));
}

/* ─── Инфо ─── */
.info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.name {
  font-weight: 600;
  font-size: 14px;
  line-height: 1.3;
  color: var(--ink);
}
.family {
  font-size: 12px;
  color: var(--ink-3);
}
.dates {
  font-size: 12px;
  color: var(--ink-2);
  display: flex;
  align-items: center;
  gap: 4px;
}
.sep { color: var(--ink-4); }
.no-dates { color: var(--ink-4); font-style: italic; }
.lifespan {
  font-size: 11px;
  color: var(--ink-3);
}
</style>
