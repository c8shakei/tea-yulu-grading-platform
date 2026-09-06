<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import echarts from '../../utils/echarts.js'

const props = defineProps({
  data: { type: Array, default: () => [] },
  title: { type: String, default: '趋势' },
  yName: { type: String, default: '数量' },
})

const chartRef = ref(null)
let chart = null

function render() {
  if (!chart) return
  const option = {
    title: { text: props.title, left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: (props.data || []).map(d => d.date) },
    yAxis: { type: 'value', name: props.yName },
    series: [
      {
        data: (props.data || []).map(d => d.count ?? d.avg_confidence ?? 0),
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.2 },
        itemStyle: { color: '#2E7D32' },
      },
    ],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
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
