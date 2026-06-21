<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import cytoscape from 'cytoscape'

const container = ref(null)
const tooltip = ref({ show: false, x: 0, y: 0, person: null })
const loading = ref(true)
const error = ref(null)
const stats = ref({ persons: 0, edges: 0 })
let cy = null

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
    elements.push({
      data: {
        id: p.id,
        label: p.full_name.split(' ').slice(0, 2).join(' '),
        full_name: p.full_name,
        sex,
        photo: p.photo,
        birth: p.birth_date,
        death: p.death_date,
        lifespan: p.lifespan,
        is_favorite: p.is_favorite,
        family_name: p.family_name,
      },
      classes: sex,
    })
  }

  for (const e of edges) {
    const cls = e.type === 'spouse' ? 'spouse' : e.type === 'sibling' ? 'sibling' : 'parent'
    elements.push({
      data: { source: e.from_id, target: e.to_id, type: e.type },
      classes: cls,
    })
  }

  if (cy) cy.destroy()

  cy = cytoscape({
    container: container.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#888',
          'background-fit': 'cover',
          'border-color': 'rgba(0,0,0,0.12)',
          'border-width': 2,
          width: 48,
          height: 48,
          shape: 'ellipse',
          label: 'data(label)',
          color: '#1a1a2e',
          'font-size': 10,
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': 6,
          'text-wrap': 'ellipsis',
          'text-max-width': 80,
          'background-opacity': 0.9,
        },
      },
      {
        selector: 'node.male',
        style: { 'background-color': '#3A6BD9', 'border-color': '#2a4fa8' },
      },
      {
        selector: 'node.female',
        style: { 'background-color': '#D94A6B', 'border-color': '#b83250' },
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
      {
        selector: 'edge.parent',
        style: { 'line-style': 'solid' },
      },
      {
        selector: 'edge.spouse',
        style: {
          'line-style': 'dashed',
          'target-arrow-shape': 'none',
          'curve-style': 'unbundled-bezier',
          'control-point-step-size': 40,
        },
      },
      {
        selector: 'edge.sibling',
        style: {
          'line-style': 'dotted',
          'target-arrow-shape': 'none',
          'curve-style': 'unbundled-bezier',
          'control-point-step-size': 20,
        },
      },
    ],
    layout: {
      name: 'cose',
      animate: false,
      nodeRepulsion: 12000,
      idealEdgeLength: 100,
      nodeDimensionsIncludeLabels: true,
    },
    wheelSensitivity: 0.3,
    minZoom: 0.3,
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
      y: pos.y - 30 / cy.zoom(),
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
    <div class="page-head">
      <h1 class="page-title">Семейное древо</h1>
      <p class="page-sub">
        Всего: <strong>{{ stats.persons }}</strong> человек,
        <strong>{{ stats.edges }}</strong> связей
      </p>
    </div>

    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <span>Загрузка дерева…</span>
    </div>
    <div v-else-if="error" class="state-msg error">
      <span>Ошибка: {{ error }}</span>
      <button class="retry-btn" @click="fetchTree">Повторить</button>
    </div>

    <div v-else ref="container" class="cy-container"></div>

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
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}
.page-head { margin-bottom: 24px; }
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}
.page-sub { font-size: 14px; color: var(--ink-3); }

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

.cy-container {
  width: 100%;
  height: 600px;
  border-radius: var(--r-lg);
  background: var(--bg-1);
  border: 1px solid var(--hairline);
  overflow: hidden;
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
