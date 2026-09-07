<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()
onMounted(() => {
  userStore.restoreToken()
})
</script>

<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background-color: #F5F5F5;
  color: #212121;
}

/* 移动端通用响应式 */
.el-card {
  max-width: 100%;
}
.el-card__body {
  word-break: break-word;
}
img, video {
  max-width: 100%;
  height: auto;
}
.el-table {
  width: 100% !important;
}
@media (max-width: 768px) {
  .el-form {
    width: 100%;
  }
  .el-form-item__label {
    float: none;
    display: block;
    text-align: left;
    margin-bottom: 4px;
  }
  .el-dialog {
    width: 90% !important;
  }
}
</style>
