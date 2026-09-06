<script setup>
import { ref, inject, computed } from 'vue'
import HashChainTimeline from '../components/charts/HashChainTimeline.vue'
import { getTrace, appendTrace } from '../api/trace'
import { ElMessage } from 'element-plus'

const schema = inject('schema')
const loading = ref(false)
const traceId = ref('')
const appendPayload = ref('')
const traceData = ref({ chain: null, valid: true })

const pageConfig = computed(() => schema.value.pages?.trace || { title: '溯源验证' })

async function onSearch() {
  if (!traceId.value) return
  loading.value = true
  try {
    const data = await getTrace(traceId.value)
    traceData.value = data
  } finally {
    loading.value = false
  }
}

async function onAppend() {
  if (!traceId.value) return
  let payload = {}
  try {
    payload = appendPayload.value ? JSON.parse(appendPayload.value) : {}
  } catch (e) {
    payload = { note: appendPayload.value }
  }
  loading.value = true
  try {
    await appendTrace(traceId.value, payload)
    ElMessage.success('复核记录已追加')
    await onSearch()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-loading="loading">
    <h2>{{ pageConfig.title }}</h2>
    <el-card shadow="hover" class="widget-card">
      <template #header>输入 trace_id</template>
      <el-input v-model="traceId" placeholder="请输入 trace_id" clearable style="width: 300px; margin-right: 12px;" />
      <el-button type="primary" @click="onSearch">查询</el-button>
      <div v-if="traceData.chain" style="margin-top: 16px;">
        <el-input v-model="appendPayload" placeholder="追加复核备注（JSON 或文本）" style="width: 300px; margin-right: 12px;" />
        <el-button @click="onAppend">追加复核</el-button>
      </div>
    </el-card>
    <HashChainTimeline :chain="traceData.chain" :valid="traceData.valid" />
  </div>
</template>

<style scoped>
.widget-card {
  margin-bottom: 16px;
}
</style>
