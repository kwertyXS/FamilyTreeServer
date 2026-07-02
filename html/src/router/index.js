import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/auth.js'
import PersonsPage from '@/views/PersonsPage.vue'
import GraphPage from '@/views/GraphPage.vue'
import EventsPage from '@/views/EventsPage.vue'
import AdminPage from '@/views/AdminPage.vue'
import PersonPage from "@/views/PersonPage.vue"
import LoginPage from "@/views/LoginPage.vue"

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { title: 'Вход', public: true }
  },
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

router.beforeEach((to, _from, next) => {
  if (to.meta.public) {
    return next()
  }
  if (!isAuthenticated()) {
    return next('/login')
  }
  next()
})

export default router
