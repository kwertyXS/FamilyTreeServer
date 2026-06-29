import { createRouter, createWebHistory } from 'vue-router'
import PersonsPage from '@/views/PersonsPage.vue'
import GraphPage from '@/views/GraphPage.vue'
import EventsPage from '@/views/EventsPage.vue'
import AdminPage from '@/views/AdminPage.vue'
import PersonPage from "@/views/PersonPage.vue";

const routes = [
  {
    path: '/',
    name: 'graph',
    component: GraphPage,
    meta: { title: 'Семейное древо' }
  },
  {
    path: '/persons',
    name: 'persons',
    component: PersonsPage,
    meta: { title: 'Список людей' }
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
    meta: {title: 'Администрирование'}
  },
  {
    path: '/person/:id',
    name: 'person',
    component: PersonPage,
    meta: {title: "Подробные данные"}
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
