<script setup>
import { ref, computed, watch } from 'vue'
import StatCards from './charts/StatCards.vue'
import GradePieChart from './charts/GradePieChart.vue'
import TrendLineChart from './charts/TrendLineChart.vue'
import ConfidenceLineChart from './charts/ConfidenceLineChart.vue'
import HashChainTimeline from './charts/HashChainTimeline.vue'
import TrainingCurvePanel from './charts/TrainingCurvePanel.vue'

const props = defineProps({
  widgets: { type: Array, default: () => [] },
  pageData: { type: Object, default: () => ({}) },
  editableJson: { type: Boolean, default: false },
})

const emit = defineEmits(['upload', 'trace-search', 'trace-append', 'json-change'])

const traceId = ref('')
const appendPayload = ref('')
const jsonText = ref('')

watch(() => props.pageData.json, (val) => {
  if (val !== undefined) jsonText.value = JSON.stringify(val, null, 2)
}, { immediate: true })

const tableData = computed(() => props.pageData.list || [])

const COLUMN_LABELS = {
  created_at: '时间',
  class_name: '等级',
  confidence: '置信度',
  trace_id: '溯源 ID',
}

function columnLabel(col) {
  return COLUMN_LABELS[col] || col
}

function handleUpload(uploadFile) {
  emit('upload', uploadFile?.raw)
}

function searchTrace() {
  emit('trace-search', traceId.value)
}

function appendTrace() {
  let payload = {}
  try {
    payload = appendPayload.value ? JSON.parse(appendPayload.value) : {}
  } catch (e) {
    payload = { note: appendPayload.value }
  }
  emit('trace-append', traceId.value, payload)
}

function applyJson() {
  try {
    const parsed = JSON.parse(jsonText.value)
    emit('json-change', parsed)
  } catch (e) {
    alert('JSON 格式错误：' + e.message)
  }
}
</script>

<template>
  <div class="schema-render">
    <template v-for="(w, idx) in widgets" :key="idx">
      <StatCards
        v-if="w.type === 'stat-card'"
        :data="pageData"
        :metrics="[w]"
      />

      <GradePieChart
        v-else-if="w.type === 'pie-chart'"
        :data="pageData[w.metric]"
        :title="w.title || '等级分布'"
      />

      <TrendLineChart
        v-else-if="w.type === 'line-chart'"
        :data="pageData[w.metric]"
        :title="w.title || '趋势'"
        :y-name="w.metric === 'confidence_trend' ? '置信度' : '数量'"
      />

      <ConfidenceLineChart
        v-else-if="w.type === 'confidence-line-chart'"
        :data="pageData[w.metric]"
        :title="w.title || '平均置信度趋势'"
      />

      <el-card v-else-if="w.type === 'image-upload'" shadow="hover" class="widget-card">
        <template #header>{{ w.title || '上传图片' }}</template>
        <el-upload drag :auto-upload="false" :on-change="handleUpload" accept="image/*">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">图片大小不超过 10MB</div>
          </template>
        </el-upload>
      </el-card>

      <el-card v-else-if="w.type === 'result-card'" shadow="hover" class="widget-card">
        <template #header>检测结果</template>
        <div v-if="pageData.result">
          <p><strong>等级：</strong>{{ pageData.result.class_name }}</p>
          <p><strong>置信度：</strong>{{ (pageData.result.confidence * 100).toFixed(2) }}%</p>
          <p><strong>边界框：</strong>{{ JSON.stringify(pageData.result.bbox) }}</p>
          <p><strong>溯源 ID：</strong>{{ pageData.result.trace_id }}</p>
        </div>
        <el-empty v-else description="暂无检测结果" />
      </el-card>

      <el-card v-else-if="w.type === 'data-table'" shadow="hover" class="widget-card">
        <template #header>{{ w.title || '数据列表' }}</template>
        <div class="table-responsive">
          <el-table :data="tableData" stripe style="min-width: 640px">
            <el-table-column
              v-for="col in w.columns"
              :key="col"
              :prop="col"
              :label="columnLabel(col)"
              show-overflow-tooltip
            />
          </el-table>
        </div>
      </el-card>

      <el-card v-else-if="w.type === 'trace-input'" shadow="hover" class="widget-card">
        <template #header>{{ w.title || '溯源查询' }}</template>
        <el-input v-model="traceId" placeholder="请输入 trace_id" clearable style="width: 300px; margin-right: 12px;" />
        <el-button type="primary" @click="searchTrace">查询</el-button>
        <div v-if="pageData.chain" style="margin-top: 16px;">
          <el-input v-model="appendPayload" placeholder="追加复核备注（JSON 或文本）" style="width: 300px; margin-right: 12px;" />
          <el-button @click="appendTrace">追加复核</el-button>
        </div>
      </el-card>

      <HashChainTimeline
        v-else-if="w.type === 'trace-chain'"
        :chain="pageData.chain"
        :valid="pageData.valid"
      />

      <el-card v-else-if="w.type === 'user-info'" shadow="hover" class="widget-card">
        <template #header>用户信息</template>
        <div v-if="pageData.user">
          <p><strong>用户名：</strong>{{ pageData.user.username }}</p>
          <p><strong>角色：</strong>{{ pageData.user.role || '用户' }}</p>
        </div>
      </el-card>

      <el-card v-else-if="w.type === 'json-viewer'" shadow="hover" class="widget-card">
        <template #header>{{ w.title || 'JSON' }}</template>
        <el-input v-model="jsonText" type="textarea" :rows="16" />
        <el-button v-if="editableJson" type="primary" style="margin-top: 12px;" @click="applyJson">应用</el-button>
      </el-card>

      <el-card v-else-if="w.type === 'image'" shadow="hover" class="widget-card">
        <template #header>{{ w.title || '图片' }}</template>
        <el-image :src="w.src" fit="contain" style="width: 100%; max-height: 500px;" />
      </el-card>

      <TrainingCurvePanel
        v-else-if="w.type === 'metrics'"
        :image-src="w.imageSrc || '/models/training_curves.png'"
        :metrics-src="w.src"
      />

      <el-card v-else shadow="hover" class="widget-card">
        <template #header>未知组件：{{ w.type }}</template>
        <pre>{{ JSON.stringify(w, null, 2) }}</pre>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.schema-render {
  padding: 20px;
}
.widget-card {
  margin-bottom: 16px;
}
.table-responsive {
  width: 100%;
  overflow-x: auto;
}
</style>
