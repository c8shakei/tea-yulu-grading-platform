<script setup>
import { ref, inject, computed } from 'vue'
import TrainingCurvePanel from '../components/charts/TrainingCurvePanel.vue'

const schema = inject('schema')
const pageConfig = computed(() => schema.value.pages?.training || { title: '训练曲线看板', widgets: [] })

const imageWidget = computed(() => pageConfig.value.widgets?.find(w => w.type === 'image') || { src: '/models/training_curves.png', title: 'W2 训练曲线' })
const metricsWidget = computed(() => pageConfig.value.widgets?.find(w => w.type === 'metrics') || { src: '/models/test_metrics.json', title: '检测指标' })
</script>

<template>
  <div>
    <h2>{{ pageConfig.title }}</h2>
    <TrainingCurvePanel :image-src="imageWidget.src" :metrics-src="metricsWidget.src" />
  </div>
</template>
