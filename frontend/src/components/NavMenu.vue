<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const props = defineProps({
  nav: { type: Array, default: () => [] },
  appName: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const mobileMenuVisible = ref(false)
const isMobile = ref(false)

const visibleNav = computed(() => {
  return props.nav.filter(item => {
    if (item.path === '/trace' || item.path === '/') return true
    return userStore.isLoggedIn()
  })
})

const activePath = computed(() => route.path)

function handleSelect(path) {
  router.push(path)
  mobileMenuVisible.value = false
}

async function handleLogout() {
  await userStore.logoutUser()
  mobileMenuVisible.value = false
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

function updateIsMobile() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  updateIsMobile()
  window.addEventListener('resize', updateIsMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateIsMobile)
})
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
    <template v-if="!isMobile">
      <el-menu-item v-for="item in visibleNav" :key="item.key" :index="item.path">
        <el-icon><component :is="iconFor(item.icon)" /></el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
    </template>
    <div class="flex-spacer"></div>
    <template v-if="!isMobile">
      <template v-if="userStore.isLoggedIn()">
        <span class="user-name">{{ userStore.user?.username }}</span>
        <el-button type="info" text @click="handleLogout">登出</el-button>
      </template>
      <template v-else>
        <el-button type="primary" text @click="$router.push('/login')">登录</el-button>
        <el-button type="primary" text @click="$router.push('/register')">注册</el-button>
      </template>
    </template>
    <el-button v-else type="primary" text class="hamburger" @click="mobileMenuVisible = true">
      <el-icon><Menu /></el-icon>
    </el-button>
  </el-menu>

  <el-drawer v-model="mobileMenuVisible" :title="appName" direction="rtl" size="70%">
    <el-menu :default-active="activePath" @select="handleSelect">
      <el-menu-item v-for="item in visibleNav" :key="item.key" :index="item.path">
        <el-icon><component :is="iconFor(item.icon)" /></el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
      <el-divider />
      <div class="drawer-actions">
        <template v-if="userStore.isLoggedIn()">
          <span class="user-name">{{ userStore.user?.username }}</span>
          <el-button type="info" text @click="handleLogout">登出</el-button>
        </template>
        <template v-else>
          <el-button type="primary" text @click="$router.push('/login')">登录</el-button>
          <el-button type="primary" text @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-menu>
  </el-drawer>
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
  overflow: hidden;
  text-overflow: ellipsis;
}
.flex-spacer {
  flex: 1;
}
.user-name {
  margin-right: 12px;
  color: #666;
}
.hamburger {
  font-size: 20px;
  padding: 8px;
}
.drawer-actions {
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.drawer-actions .el-button {
  justify-content: flex-start;
}
@media (max-width: 768px) {
  .nav-menu {
    padding: 0 12px;
  }
  .brand {
    font-size: 14px;
    margin-right: 8px;
  }
}
</style>
