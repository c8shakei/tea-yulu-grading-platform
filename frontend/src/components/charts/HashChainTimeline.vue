<script setup>
import { computed } from 'vue'

const props = defineProps({
  chain: { type: Array, default: () => [] },
  valid: { type: Boolean, default: true },
})

const items = computed(() => (props.chain || []).map((block, index) => ({
  index,
  ...block,
  shortHash: block.hash ? `${block.hash.slice(0, 16)}...` : '',
  shortPrev: block.prev_hash ? `${block.prev_hash.slice(0, 16)}...` : '无',
})))
</script>

<template>
  <el-alert
    v-if="items.length"
    :title="valid ? '哈希链验证通过' : '哈希链存在篡改'"
    :type="valid ? 'success' : 'error'"
    :closable="false"
    style="margin-bottom: 16px;"
  />
  <el-timeline>
    <el-timeline-item
      v-for="item in items"
      :key="item.index"
      :type="valid ? 'primary' : 'danger'"
      :timestamp="new Date(item.timestamp * 1000).toLocaleString()"
    >
      <el-card :class="['chain-card', { tampered: !valid }]">
        <p><strong>区块 #{{ item.index }}</strong></p>
        <p>当前哈希：{{ item.shortHash }}</p>
        <p>上一区块哈希：{{ item.shortPrev }}</p>
        <p>载荷：{{ JSON.stringify(item.payload) }}</p>
      </el-card>
    </el-timeline-item>
  </el-timeline>
</template>

<style scoped>
.chain-card {
  margin-bottom: 8px;
}
.chain-card.tampered {
  border: 1px solid #F56C6C;
  background-color: #FEF0F0;
}
.chain-card p {
  margin: 4px 0;
  font-size: 13px;
  word-break: break-all;
}
</style>
