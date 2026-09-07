<script setup>
import { ref, onMounted, provide } from 'vue'
import NavMenu from '../components/NavMenu.vue'
import { getSchema } from '../api/schema'

const schema = ref({
  appName: '恩施玉露茶品质分级与溯源平台',
  version: '0.3.0',
  theme: { primary: '#2E7D32', secondary: '#81C784', background: '#F5F5F5', text: '#212121' },
  nav: [],
  pages: {},
})

provide('schema', schema)

onMounted(async () => {
  try {
    const data = await getSchema()
    schema.value = data
    document.title = data.appName
  } catch (e) {
    console.error('加载 UI Schema 失败', e)
  }
})
</script>

<template>
  <div class="main-layout">
    <NavMenu :nav="schema.nav" :app-name="schema.appName" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
  padding: 20px;
  max-width: 100%;
  box-sizing: border-box;
}
@media (max-width: 768px) {
  .main-content {
    padding: 12px;
  }
}
</style>
