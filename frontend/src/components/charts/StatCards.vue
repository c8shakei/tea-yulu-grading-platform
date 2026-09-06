<script setup>
defineProps({
  data: { type: Object, default: () => ({}) },
  metrics: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="stat-cards">
    <el-card v-for="m in metrics" :key="m.metric" class="stat-card" shadow="hover">
      <div class="stat-value">{{ data[m.metric] ?? 0 }}</div>
      <div class="stat-title">{{ m.title || m.metric }}</div>
    </el-card>
  </div>
</template>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.stat-card {
  text-align: center;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #2E7D32;
}
.stat-title {
  margin-top: 8px;
  color: #666;
}
</style>
