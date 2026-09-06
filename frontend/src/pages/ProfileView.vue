<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import GradePieChart from '../components/charts/GradePieChart.vue'
import ConfidenceLineChart from '../components/charts/ConfidenceLineChart.vue'
import StatCards from '../components/charts/StatCards.vue'
import { getMe } from '../api/auth'
import { getUserStats } from '../api/stats'
import { useUserStore } from '../stores/user'
import { removeToken } from '../utils/auth'

const schema = inject('schema')
const userStore = useUserStore()
const router = useRouter()
const loading = ref(false)
const userInfo = ref(null)
const userStats = ref({})

const pageConfig = computed(() => schema.value.pages?.profile || { title: '个人中心' })

async function loadData() {
  loading.value = true
  try {
    userInfo.value = await getMe()
    if (userInfo.value?.user_id) {
      userStats.value = await getUserStats(userInfo.value.user_id)
    }
  } finally {
    loading.value = false
  }
}

function logout() {
  removeToken()
  userStore.logoutUser()
  router.push('/login')
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading">
    <h2>{{ pageConfig.title }}</h2>
    <el-card shadow="hover" class="widget-card">
      <template #header>用户信息</template>
      <p><strong>用户名：</strong>{{ userInfo?.username || '' }}</p>
      <p><strong>角色：</strong>{{ userInfo?.role || '用户' }}</p>
    </el-card>
    <StatCards :data="userStats" :metrics="[{ metric: 'total_detections', title: '总检测数' }]" />
    <GradePieChart :data="userStats.grade_distribution || []" title="个人等级分布" />
    <ConfidenceLineChart :data="userStats.confidence_trend || []" title="平均置信度趋势" />
    <el-button type="danger" style="margin-left: 20px;" @click="logout">登出</el-button>
  </div>
</template>

<style scoped>
.widget-card {
  margin-bottom: 16px;
}
</style>
