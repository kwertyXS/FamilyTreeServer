import { createRouter, createWebHistory } from 'vue-router'
import GraphPage from '@/views/GraphPage.vue'
import EventsPage from '@/views/EventsPage.vue'
import AdminPage from '@/views/AdminPage.vue'

const routes = [
  {
    path: '/',
    name: 'graph',
    component: GraphPage,
    meta: { title: 'Семейное древо' }
  },
  {
    path: '/events',
    name: 'events',
    component: EventsPage,
    meta: { title: 'Хронология событий' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminPage,
    meta: { title: 'Администрирование' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
