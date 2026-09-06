<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const props = defineProps({
  nav: { type: Array, default: () => [] },
  appName: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const visibleNav = computed(() => {
  return props.nav.filter(item => {
    if (item.path === '/trace' || item.path === '/') return true
    return userStore.isLoggedIn()
  })
})

const activePath = computed(() => route.path)

function handleSelect(path) {
  router.push(path)
}

async function handleLogout() {
  await userStore.logoutUser()
  router.push('/login')
}

function iconFor(key) {
  const map = {
    DashboardOutlined: 'DataLine',
    CameraOutlined: 'Camera',
    HistoryOutlined: 'Clock',
    SafetyCertificateOutlined: 'CircleCheck',
    UserOutlined: 'User',
    CodeOutlined: 'Code',
    LineChartOutlined: 'TrendCharts',
  }
  return map[key] || 'Menu'
}
</script>

<template>
  <el-menu
    :default-active="activePath"
    class="nav-menu"
    mode="horizontal"
    :ellipsis="false"
    @select="handleSelect"
  >
    <div class="brand">{{ appName }}</div>
    <el-menu-item v-for="item in visibleNav" :key="item.key" :index="item.path">
      <el-icon><component :is="iconFor(item.icon)" /></el-icon>
      <span>{{ item.label }}</span>
    </el-menu-item>
    <div class="flex-spacer"></div>
    <template v-if="userStore.isLoggedIn()">
      <span class="user-name">{{ userStore.user?.username }}</span>
      <el-button type="info" text @click="handleLogout">登出</el-button>
    </template>
    <template v-else>
      <el-button type="primary" text @click="$router.push('/login')">登录</el-button>
      <el-button type="primary" text @click="$router.push('/register')">注册</el-button>
    </template>
  </el-menu>
</template>

<style scoped>
.nav-menu {
  padding: 0 20px;
  align-items: center;
}
.brand {
  font-size: 18px;
  font-weight: bold;
  color: #2E7D32;
  margin-right: 24px;
  white-space: nowrap;
}
.flex-spacer {
  flex: 1;
}
.user-name {
  margin-right: 12px;
  color: #666;
}
</style>
