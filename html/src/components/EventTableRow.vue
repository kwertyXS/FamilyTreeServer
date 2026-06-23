<script setup>
defineProps({
  event: {
    type: Object,
    required: true
  }
})

/** Возвращает иконку SVG по типу события */
function eventIcon(type) {
  const icons = {
    'Рождение':    'M12 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0 10c-4 0-6 2-6 6h12c0-4-2-6-6-6z',
    'Смерть':      'M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm-2 5l4 4-4 4',
    'Брак':        'M6 21l12-12M8 3l4 4-4 4M14 9l4 4-4 4',
    'Свадьба':     'M6 21l12-12M8 3l4 4-4 4M14 9l4 4-4 4',
    'Венчание':    'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
    'Крещение':    'M12 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm0 8c-3 0-5 1.5-5 4h10c0-2.5-2-4-5-4z',
  }
  return icons[type] || 'M12 22s-7-7.58-7-13a7 7 0 1 1 14 0c0 5.42-7 13-7 13zM12 9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z'
}
</script>

<template>
  <tr class="event-row">
    <!-- Тип + иконка -->
    <td class="cell-type">
      <span class="type-flex">
        <span class="type-icon-wrap" :title="event.type">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path :d="eventIcon(event.type)"/>
          </svg>
        </span>
        <span class="type-label">{{ event.type }}</span>
      </span>
    </td>

    <!-- Человек -->
    <td class="cell-person">
      <span v-if="event.person" class="person-text">{{ event.person.full_name }}</span>
      <span v-else class="no-date">—</span>
    </td>

    <!-- Дата -->
    <td class="cell-date">
      <span v-if="event.date" class="date-text">{{ event.date }}</span>
      <span v-else class="no-date">—</span>
    </td>

    <!-- Описание -->
    <td class="cell-desc">
      <span v-if="event.description" class="desc-text">{{ event.description }}</span>
      <span v-else class="no-desc">—</span>
    </td>

    <!-- Место -->
    <td class="cell-place">
      <template v-if="event.place">
        <span class="place-flex">
          <svg class="place-icon" width="12" height="12" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s-7-7.58-7-13a7 7 0 1 1 14 0c0 5.42-7 13-7 13z"/>
            <circle cx="12" cy="9" r="2.5"/>
          </svg>
          <span class="place-name">{{ event.place.full_name }}</span>
        </span>
      </template>
      <span v-else class="no-place">—</span>
    </td>
  </tr>
</template>

<style scoped>
.event-row {
  transition: background .15s var(--ease-out);
}
.event-row:hover {
  background: var(--tint-tr);
}

.event-row td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--hairline);
  vertical-align: middle;
  font-size: 13px;
  color: var(--ink);
}

/* ─── Тип ─── */
.cell-type {
  white-space: nowrap;
}
.type-flex {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.type-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--glass-thin);
  border: 1px solid var(--edge-hi);
  color: var(--tint);
  flex-shrink: 0;
}
.type-label {
  font-weight: 500;
}

/* ─── Дата ─── */
.cell-date {
  white-space: nowrap;
  color: var(--ink-2);
  font-variant-numeric: tabular-nums;
}
.no-date { color: var(--ink-4); }

/* ─── Описание ─── */
.cell-desc {
  max-width: 280px;
}
.desc-text {
  line-height: 1.4;
}
.no-desc { color: var(--ink-4); }

/* ─── Место ─── */
.cell-place {
  white-space: nowrap;
}
.place-flex {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.place-icon {
  flex-shrink: 0;
  color: var(--tint);
}
.place-name {
  color: var(--ink-2);
}
.no-place { color: var(--ink-4); }
</style>
