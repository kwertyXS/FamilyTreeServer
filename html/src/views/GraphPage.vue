<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import template from '../components/GraphCard.svg?raw'
import malePlaceholder from '../components/placeholder-male.svg?raw'
import femalePlaceholder from '../components/placeholder-female.svg?raw'
import router from "@/router/index.js";
cytoscape.use(dagre)

const container = ref(null)
const loading = ref(true)
const error = ref(null)
const stats = ref({ persons: 0, edges: 0 })
const searchQuery = ref('')
const searchResult = ref('')
const nodePositions = ref([])
const cardSize = ref(calcCardSize())
const cardFont = ref(calcCardFont())

const base_ip = window.location.origin
let cy = null
let animFrameId = null


function applyTemplate(svg, data) {
  return svg.replace(/{{(.*?)}}/g, (_, key) => data[key.trim()] ?? '')
}


function calcCardSize() {
  const vw = window.innerWidth
  return Math.max(45, Math.min(90, Math.round(vw * 90 / 1920)))
}
function calcCardFont() {
  const s = calcCardSize()
  return Math.round(s * 10 / 60) + 'px'
}

function handleResize() {
  cardSize.value = calcCardSize()
  cardFont.value = calcCardFont()
}

/** Множество ID подсвеченных узлов */
const highlightedIds = ref(new Set())


function onSearch() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q || !cy) return

  highlightedIds.value = new Set()

  const matching = cy.nodes().filter(n =>
    n.data('full_name').toLowerCase().includes(q)
  )

  // Сбросить выделение с предыдущих узлов
  cy.nodes().removeClass('highlight')

  if (matching.length > 0) {
    highlightedIds.value = new Set(matching.map(n => n.id()))
    matching.addClass('highlight')

    // Плавно центрируем камеру на найденных узлах
    const bb = matching.boundingBox()
    const pad = 40
    const cw = cy.width()
    const ch = cy.height()
    const zoom = Math.min(cy.maxZoom(), Math.max(0.2,
      Math.min(cw / (bb.w + pad * 2), ch / (bb.h + pad * 2))
    ))
    cy.animate({
      pan: {
        x: cw / 2 - (bb.x1 + bb.x2) / 2 * zoom,
        y: ch / 2 - (bb.y1 + bb.y2) / 2 * zoom,
      },
      zoom,
      duration: 500,
    })

    searchResult.value = `Найдено: ${matching.length}`
  } else {
    searchResult.value = 'Ничего не найдено'
  }
}


function clearSearch() {
  searchQuery.value = ''
  searchResult.value = ''
  highlightedIds.value = new Set()
  cy?.nodes().removeClass('highlight')
  cy?.nodes().stop()
  scheduleUpdate()
}


function svgToDataUrl(svg) {
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
}


async function photoToDataUrl(path) {
  try {
    const res = await fetch(path)
    const blob = await res.blob()
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.readAsDataURL(blob)
    })
  } catch {
    return ''
  }
}


async function fetchTree() {
  loading.value = true
  error.value = null
  try {
    const res = await axios.get('/api/tree')
    const persons = res.data.persons

    // Предзагружаем фото как base64, чтоб не было проблем с CORS/null origin внутри SVG
    await Promise.all(persons.map(async (p) => {
      if (p.photo) {
        p.photoDataUrl = await photoToDataUrl(`${base_ip}/photos/${p.photo}`)
      }
    }))

    stats.value = { persons: persons.length, edges: res.data.edges.length }
    loading.value = false
    await nextTick()
    renderGraph(persons, res.data.edges)
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
        full_name: p.full_name,
        sex,
        photo: p.photo,
        photoDataUrl: p.photoDataUrl || '',
        birth: p.birth_date,
        death: p.death_date,
        lifespan: p.lifespan,
        is_favorite: p.is_favorite,
        family_name: p.family_name,
      },
    })
  }

  for (const e of edges) {
    if (e.type === 'parent') {
      elements.push({ data: { source: e.from_id, target: e.to_id }, classes: 'parent' })
    } else if (e.type === 'spouse') {
      elements.push({ data: { source: e.from_id, target: e.to_id }, classes: 'spouse' })
    }
  }

  if (cy) cy.destroy()

  const spouseConstraints = []
  for (const e of edges) {
    if (e.type === 'spouse') {
      spouseConstraints.push({ type: 'same', nodes: [e.from_id, e.to_id] })
    }
  }

  // Для каждой пары родителей (общий ребёнок) — один уровень
  const parentsByChild = {}
  for (const e of edges) {
    if (e.type === 'parent') {
      if (!parentsByChild[e.to_id]) parentsByChild[e.to_id] = []
      parentsByChild[e.to_id].push(e.from_id)
    }
  }
  const parentConstraints = []
  const seen = new Set()
  for (const childId in parentsByChild) {
    const parents = parentsByChild[childId]
    for (let i = 0; i < parents.length - 1; i++) {
      for (let j = i + 1; j < parents.length; j++) {
        const key = [parents[i], parents[j]].sort().join('|')
        if (!seen.has(key)) {
          seen.add(key)
          parentConstraints.push({ type: 'same', nodes: [parents[i], parents[j]] })
        }
      }
    }
  }
  const allConstraints = [...spouseConstraints, ...parentConstraints]

  cy = cytoscape({
    container: container.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          shape: 'round-rectangle',
          'background-color': 'transparent',
          'background-fit': 'contain',
          'background-image': (ele) => {
            const d = ele.data()
            var photo = ""
            if (d.photo && d.photoDataUrl){
              photo = d.photoDataUrl
            } else if (d.sex === 'male') {
              photo = svgToDataUrl(malePlaceholder)
            } else if (d.sex === 'female') {
              photo = svgToDataUrl(femalePlaceholder)
            } else {
              photo = svgToDataUrl(malePlaceholder)
            }

            const svg = applyTemplate(template, {
              full_name: d.full_name,
              family_name: d.family_name || '',
              photos: photo,
              birth_date: d.birth || '…',
              death_date: d.death || '…',
              lifespan: d.lifespan || '',
              sex: d.sex || '',
              is_favorite: d.is_favorite ? 'true' : '',
            })

            return svgToDataUrl(svg)
          },
          width: 200,
          height: 260,
          label: '',
        },
      },

      {
        selector: 'node.highlight',
        style: {
          'border-color': '#F5A623',
          'border-width': 3,
          'border-opacity': 1,
        },
      },

      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#b0b0c0',
          'curve-style': 'taxi',
          'taxi-turn': 40,
          'taxi-turn-min-distance': 15,
          'taxi-direction': 'downward',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#b0b0c0',
          'arrow-scale': 0.7,
        },
      },

      {
        selector: 'edge.spouse',
        style: {
          opacity: 0,
          width: 0,
          'target-arrow-shape': 'none',
        },
      },
    ],

    layout: {
      name: 'dagre',
      rankDir: 'TB',
      rankConstraints: allConstraints.length ? allConstraints : undefined,
      spacingFactor: 1.1,
      nodeSep: 30,
      rankSep: 80,
      animate: false,
    },
    minZoom: 0.15,
    maxZoom: 2.5,
  })


  cy.on('layoutstop', () => {
    cy.fit(undefined, 80)
    // scheduleUpdate()
  })

  cy.on('tap', 'node', (evt) => {
    router.push(`/person/${evt.target.id()}`)
  })
}


onMounted(() => {
  window.addEventListener('resize', handleResize)
  fetchTree()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animFrameId)
  if (cy) cy.destroy()
})
</script>

<template>
  <div class="graph-page">
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

    <!-- Статистика -->
    <div v-if="!loading && !error" class="graph-stats glass">
      <strong>{{ stats.persons }}</strong> чел.,
      <strong>{{ stats.edges }}</strong> связей
    </div>

    <!-- Поиск -->
    <div v-if="!loading && !error" class="graph-search glass">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="Поиск человека…"
        @keydown.enter="onSearch"
      />
      <button class="search-btn" @click="onSearch">Найти</button>
      <span v-if="searchResult" class="search-result" :class="{ 'search-result--empty': searchResult === 'Ничего не найдено' }">{{ searchResult }}</span>
      <button v-if="searchQuery" class="search-clear" @click="clearSearch" title="Очистить">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
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
}
.cyHidden {
  visibility: hidden;
  pointer-events: none;
}

/* ─── Оверлей узлов ─── */
.nodes-overlay {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}
.node-wrapper {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: auto;
  cursor: pointer;
  transition: filter .2s var(--ease-out), box-shadow .2s var(--ease-out);
}
.node-wrapper:hover {
  z-index: 10;
}
.node-wrapper--highlight {
  filter: drop-shadow(0 0 12px rgba(245,166,35,0.6));
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
.graph-overlay--error { color: #D94A6B; }
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

/* ─── Поиск ─── */
.graph-search {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 6px 6px 12px;
  border-radius: var(--r-pill);
  z-index: 5;
}
.search-icon { flex-shrink: 0; color: var(--ink-3); }
.search-input {
  flex: 0 1 220px;
  border: none;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: var(--ink);
  font-family: inherit;
}
.search-input::placeholder { color: var(--ink-4); }
.search-btn {
  padding: 5px 14px;
  border-radius: var(--r-pill);
  border: none;
  background: var(--tint);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background .15s var(--ease-out);
  white-space: nowrap;
}
.search-btn:hover { background: var(--tint-2); }
.search-result { font-size: 12px; color: var(--ink-3); white-space: nowrap; }
.search-result--empty { color: #D94A6B; }
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
.search-clear:hover { background: var(--glass-thick); color: var(--ink); }
</style>

<style>
/* ─── Стили карточки узла (v-html — нужен unscoped) ─── */
.node-card {
  display: flex;
  flex-direction: column;
  background: var(--glass-regular);
  backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid var(--edge-hi);
  border-bottom-color: var(--edge-lo);
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(20,16,10,0.08);
}
.node-card__photo {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--bg-1);
}
.node-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.node-card__placeholder {
  display: block;
  width: 100%;
  height: 100%;
}
.node-card__sex {
  position: absolute;
  bottom: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  background: var(--glass-thick);
  backdrop-filter: blur(8px);
  border: 1px solid var(--edge-hi);
  line-height: 1;
}
.node-card__sex[data-sex="male"]   { color: #3A6BD9; }
.node-card__sex[data-sex="female"] { color: #D94A6B; }
.node-card__star {
  position: absolute;
  top: 2px;
  right: 2px;
  color: #F5A623;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));
  line-height: 1;
}
.node-card__name {
  font-weight: 600;
  color: var(--ink);
  text-align: center;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-card__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 5px;
  background: rgba(255,255,255,0.5);
}
.node-card__family {
  color: var(--ink-3);
  text-align: center;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.node-card__dates {
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--ink-2);
  line-height: 1.2;
}
.node-card__sep { color: var(--ink-4); }
.node-card__lifespan {
  color: var(--ink-3);
  text-align: center;
  line-height: 1.2;
}
</style>