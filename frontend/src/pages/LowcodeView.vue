<script setup>
import { ref, inject, computed, onMounted } from 'vue'
import SchemaRender from '../components/SchemaRender.vue'

const schema = inject('schema')
const jsonText = ref('')

const pageConfig = computed(() => schema.value.pages?.lowcode || { title: '低代码演示', widgets: [] })

onMounted(() => {
  jsonText.value = JSON.stringify(schema.value, null, 2)
})

function applySchema() {
  try {
    const parsed = JSON.parse(jsonText.value)
    schema.value = parsed
  } catch (e) {
    alert('JSON 格式错误：' + e.message)
  }
}
</script>

<template>
  <div>
    <h2>{{ pageConfig.title }}</h2>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>JSON 编辑器</template>
          <el-input v-model="jsonText" type="textarea" :rows="24" />
          <el-button type="primary" style="margin-top: 12px;" @click="applySchema">应用</el-button>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>实时预览</template>
          <SchemaRender :widgets="pageConfig.widgets" :page-data="{ json: schema }" editable-json @json-change="schema.value = $event" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
