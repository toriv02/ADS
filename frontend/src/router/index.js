import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import TasksView from '../views/TasksView.vue'
import AddTaskView from '../views/AddTaskView.vue'
import TaskDetailView from '../views/TaskDetailView.vue'

const routes = [
  { path: '/login', name: 'Login', component: LoginView, meta: { requiresAuth: false } },
  { path: '/', name: 'Tasks', component: TasksView, meta: { requiresAuth: true } },
  { path: '/tasks/new', name: 'AddTask', component: AddTaskView, meta: { requiresAuth: true } },
  { path: '/tasks/:id', name: 'TaskDetail', component: TaskDetailView, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router