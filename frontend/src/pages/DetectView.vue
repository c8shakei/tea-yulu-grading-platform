<script setup>
import { ref, inject, computed } from 'vue'
import SchemaRender from '../components/SchemaRender.vue'
import { detectImage } from '../api/detect'

const schema = inject('schema')
const loading = ref(false)
const result = ref(null)

const pageConfig = computed(() => schema.value.pages?.detect || { title: '检测工作台', widgets: [] })
const pageData = computed(() => ({ result: result.value }))

async function onUpload(file) {
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    alert('图片大小不能超过 10MB')
    return
  }
  loading.value = true
  try {
    result.value = await detectImage(file)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-loading="loading">
    <h2>{{ pageConfig.title }}</h2>
    <SchemaRender :widgets="pageConfig.widgets" :page-data="pageData" @upload="onUpload" />
  </div>
</template>
