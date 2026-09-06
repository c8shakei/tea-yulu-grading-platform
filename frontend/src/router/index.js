import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../pages/DashboardView.vue'),
        meta: { public: true },
      },
      {
        path: '/detect',
        name: 'Detect',
        component: () => import('../pages/DetectView.vue'),
      },
      {
        path: '/history',
        name: 'History',
        component: () => import('../pages/HistoryView.vue'),
      },
      {
        path: '/trace',
        name: 'Trace',
        component: () => import('../pages/TraceView.vue'),
        meta: { public: true },
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('../pages/ProfileView.vue'),
      },
      {
        path: '/lowcode',
        name: 'Lowcode',
        component: () => import('../pages/LowcodeView.vue'),
      },
      {
        path: '/training',
        name: 'Training',
        component: () => import('../pages/TrainingView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isPublic = to.meta?.public
  if (!isPublic && !userStore.isLoggedIn() && !userStore.loading) {
    next('/login')
  } else {
    next()
  }
})

export default router
