<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import SchemaRender from '../components/SchemaRender.vue'
import { getDetections } from '../api/detect'
import { getUserStats } from '../api/stats'
import { useUserStore } from '../stores/user'

const schema = inject('schema')
const userStore = useUserStore()
const loading = ref(false)
const detections = ref([])
const userStats = ref({})

const pageConfig = computed(() => schema.value.pages?.history || { title: '历史记录', widgets: [] })
const pageData = computed(() => ({
  list: detections.value,
  grade_distribution: userStats.value.grade_distribution || [],
  confidence_trend: userStats.value.confidence_trend || [],
}))

async function loadData() {
  loading.value = true
  try {
    detections.value = await getDetections()
    if (userStore.user?.user_id) {
      userStats.value = await getUserStats(userStore.user.user_id)
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading">
    <h2>{{ pageConfig.title }}</h2>
    <SchemaRender :widgets="pageConfig.widgets" :page-data="pageData" />
  </div>
</template>
