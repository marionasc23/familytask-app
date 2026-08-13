import { createRouter, createWebHistory } from 'vue-router'
import { getMe, isLogged } from './api.js'
import Login from './views/Login.vue'
import Signup from './views/Signup.vue'
import TasksView from './views/TasksView.vue'
import FamilyView from './views/FamilyView.vue'
import ChatAssistant from './views/ChatAssistant.vue'

const routes = [
  { path: '/', redirect: '/taches' },
  { path: '/login', component: Login },
  { path: '/signup', component: Signup },
  { path: '/taches', component: TasksView, meta: { auth: true, nav: true } },
  { path: '/assistant', component: ChatAssistant, meta: { auth: true, nav: true } },
  { path: '/famille', component: FamilyView, meta: { auth: true, nav: true, admin: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.auth && !isLogged()) return '/login'
  if (to.meta.admin && !(getMe() && getMe().is_admin)) return '/taches'
  if ((to.path === '/login' || to.path === '/signup') && isLogged()) return '/taches'
})

export default router
