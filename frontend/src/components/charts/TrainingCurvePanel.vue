<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  imageSrc: { type: String, default: '' },
  metricsSrc: { type: String, default: '' },
})

const metrics = ref({})
const loading = ref(false)

onMounted(async () => {
  if (!props.metricsSrc) return
  loading.value = true
  try {
    const res = await fetch(props.metricsSrc)
    metrics.value = await res.json()
  } catch (e) {
    metrics.value = { error: '加载指标失败' }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="16">
      <el-card shadow="hover" class="chart-card">
        <template #header>W2 训练曲线</template>
        <el-image :src="imageSrc" fit="contain" style="width: 100%; height: 400px;" />
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card shadow="hover" class="chart-card">
        <template #header>测试指标</template>
        <el-skeleton v-if="loading" :rows="6" />
        <pre v-else class="metrics-pre">{{ JSON.stringify(metrics, null, 2) }}</pre>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.chart-card {
  margin-bottom: 16px;
}
.metrics-pre {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  background: #f8f8f8;
  padding: 12px;
  border-radius: 4px;
}
</style>
