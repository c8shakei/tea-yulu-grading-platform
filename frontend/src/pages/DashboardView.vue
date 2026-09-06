<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import SchemaRender from '../components/SchemaRender.vue'
import { getStatsOverview } from '../api/stats'

const schema = inject('schema')
const loading = ref(false)
const stats = ref({})

const pageConfig = computed(() => schema.value.pages?.dashboard || { title: '首页仪表盘', widgets: [] })
const pageData = computed(() => stats.value)

async function loadData() {
  loading.value = true
  try {
    stats.value = await getStatsOverview()
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
