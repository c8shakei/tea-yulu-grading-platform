<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import echarts from '../../utils/echarts.js'

const props = defineProps({
  data: { type: Array, default: () => [] },
  title: { type: String, default: '等级分布' },
})

const chartRef = ref(null)
let chart = null

function render() {
  if (!chart) return
  const option = {
    title: { text: props.title, left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}: {c} ({d}%)' },
        data: props.data || [],
      },
    ],
  }
  chart.setOption(option, true)
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    render()
    window.addEventListener('resize', chart.resize)
  }
})

onUnmounted(() => {
  if (chart) {
    window.removeEventListener('resize', chart.resize)
    chart.dispose()
    chart = null
  }
})

watch(() => props.data, render, { deep: true })
</script>

<template>
  <el-card shadow="hover" class="chart-card">
    <template #header>{{ title }}</template>
    <div ref="chartRef" class="chart"></div>
  </el-card>
</template>

<style scoped>
.chart-card {
  margin-bottom: 16px;
}
.chart {
  width: 100%;
  height: 320px;
}
</style>
