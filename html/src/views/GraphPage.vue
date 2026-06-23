<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'

cytoscape.use(dagre)

const container = ref(null)
const tooltip = ref({ show: false, x: 0, y: 0, person: null })
const loading = ref(true)
const error = ref(null)
const stats = ref({ persons: 0, edges: 0 })
let cy = null

/** Гендерная SVG-заглушка в формате data URI */
function placeholderDataUri(sex) {
  const color = sex === 'male' ? '#3A6BD9' : sex === 'female' ? '#D94A6B' : '#888'
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect width="100" height="100" fill="${color}"/>
    <circle cx="50" cy="32" r="18" fill="#fff" opacity=".35"/>
    <path d="M22 82 Q50 55 78 82" fill="#fff" opacity=".35"/>
  </svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

async function fetchTree() {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get('/api/tree')
    stats.value = { persons: res.data.persons.length, edges: res.data.edges.length }
    loading.value = false
    await nextTick()
    renderGraph(res.data.persons, res.data.edges)
  } catch (e) {
    error.value = e.message
    loading.value = false
  }
}

function renderGraph(persons, edges) {
  if (!container.value) return

  const elements = []

  for (const p of persons) {
    const sex = p.sex === true ? 'male' : p.sex === false ? 'female' : 'unknown'
    const photoUrl = p.photo ? `/photos/${p.photo}` : placeholderDataUri(sex)
    const borderCls = sex === 'male' ? 'male' : sex === 'female' ? 'female' : ''

    elements.push({
      data: {
        id: p.id,
        label: p.full_name,
        full_name: p.full_name,
        sex,
        photo: photoUrl,
        birth: p.birth_date,
        death: p.death_date,
        lifespan: p.lifespan,
        is_favorite: p.is_favorite,
        family_name: p.family_name,
      },
      classes: borderCls,
    })
  }

  for (const e of edges) {
    if (e.type === 'parent') {
      elements.push({
        data: { source: e.from_id, target: e.to_id },
        classes: 'parent',
      })
    }
  }

  if (cy) cy.destroy()

  cy = cytoscape({
    container: container.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          shape: 'rectangle',
          width: 90,
          height: 115,
          'background-color': '#888',
          'background-image': 'data(photo)',
          'background-fit': 'cover',
          'background-position-x': '50%',
          'background-position-y': '0%',
          'border-color': 'rgba(0,0,0,0.15)',
          'border-width': 2,
          label: 'data(label)',
          color: '#1a1a2e',
          'font-size': 10,
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': 5,
          'text-wrap': 'ellipsis',
          'text-max-width': 84,
          'text-background-color': '#ffffff',
          'text-background-opacity': 0.92,
          'text-background-padding': 4,
          'text-background-shape': 'roundrectangle',
          'min-zoomed-font-size': 7,
        },
      },
      {
        selector: 'node.male',
        style: { 'border-color': '#2a4fa8' },
      },
      {
        selector: 'node.female',
        style: { 'border-color': '#b83250' },
      },
      {
        selector: 'node[is_favorite = true]',
        style: { 'border-width': 3, 'border-color': '#F5A623' },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#b0b0c0',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#b0b0c0',
          'arrow-scale': 0.7,
        },
      },
    ],
    layout: {
      name: 'dagre',
      rankDir: 'TB',
      spacingFactor: 1.4,
      nodeSep: 40,
      rankSep: 100,
      animate: false,
    },
    wheelSensitivity: 0.3,
    minZoom: 0.1,
    maxZoom: 3,
  })

  cy.on('layoutstop', () => {
    cy.fit(undefined, 50)
  })

  // Tooltip
  cy.on('mouseover', 'node', (ev) => {
    const node = ev.target
    const d = node.data()
    const pos = node.renderedPosition()
    tooltip.value = {
      show: true,
      x: pos.x,
      y: pos.y - 20 / cy.zoom(),
      person: d,
    }
    document.body.style.cursor = 'pointer'
  })
  cy.on('mouseout', 'node', () => {
    tooltip.value.show = false
    document.body.style.cursor = ''
  })
}

onMounted(fetchTree)
onBeforeUnmount(() => { if (cy) cy.destroy() })
</script>

<template>
  <div class="graph-page">
    <!-- Контейнер графа (всегда смонтирован, скрыт пока загрузка) -->
    <div ref="container" class="cy-container" :class="{ cyHidden: loading || error }"></div>

    <!-- Загрузка -->
    <div v-if="loading" class="graph-overlay">
      <div class="spinner"></div>
      <span>Загрузка дерева…</span>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="graph-overlay graph-overlay--error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchTree">Повторить</button>
    </div>

    <!-- Статистика в углу -->
    <div v-if="!loading && !error" class="graph-stats glass">
      <strong>{{ stats.persons }}</strong> чел.,
      <strong>{{ stats.edges }}</strong> связей
    </div>

    <Teleport to="body">
      <div
        v-if="tooltip.show"
        class="cy-tooltip glass"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <div class="tip-name">{{ tooltip.person.full_name }}</div>
        <div class="tip-dates">
          {{ tooltip.person.birth || '…' }} — {{ tooltip.person.death || '…' }}
        </div>
        <div v-if="tooltip.person.lifespan" class="tip-lifespan">
          {{ tooltip.person.lifespan }}
        </div>
        <div v-if="tooltip.person.family_name" class="tip-family">
          {{ tooltip.person.family_name }}
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.graph-page {
  position: fixed;
  inset: 0;
  z-index: 0;
}

.cy-container {
  width: 100%;
  height: 100%;
  background: var(--bg-1);
}
.cyHidden {
  visibility: hidden;
  pointer-events: none;
}

/* ─── Оверлей загрузки / ошибки ─── */
.graph-overlay {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--ink-2);
  font-size: 15px;
}
.graph-overlay--error {
  color: #D94A6B;
}
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

/* ─── Статистика ─── */
.graph-stats {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 18px;
  border-radius: var(--r-pill);
  font-size: 13px;
  color: var(--ink-2);
  z-index: 5;
  white-space: nowrap;
}
</style>

<style>
.cy-tooltip {
  position: fixed;
  transform: translate(-50%, -100%);
  padding: 10px 14px;
  border-radius: var(--r-sm);
  z-index: 9999;
  pointer-events: none;
  white-space: nowrap;
  line-height: 1.4;
}
.tip-name { font-weight: 600; font-size: 13px; color: var(--ink); }
.tip-dates { font-size: 12px; color: var(--ink-3); }
.tip-lifespan,
.tip-family { font-size: 11px; color: var(--ink-4); }
</style>
