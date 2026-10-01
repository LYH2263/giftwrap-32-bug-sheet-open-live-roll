<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'

const items = ref([])
const err = ref('')
const drafts = ref({})
const saving = ref(null)

async function load() {
  items.value = (await getJSON('/api/papers')).items
  for (const p of items.value) drafts.value[p.id] = String(p.roll_width)
}

onMounted(async () => {
  try {
    await load()
  } catch (e) {
    err.value = String(e.message || e)
  }
})

async function save(p) {
  err.value = ''
  const v = Number(drafts.value[p.id])
  if (!(v > 0)) {
    err.value = `${p.name}：卷宽必须大于 0`
    return
  }
  saving.value = p.id
  try {
    await putJSON(`/api/papers/${p.id}`, { roll_width: v })
    await load()
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    saving.value = null
  }
}
</script>

<template>
  <div class="page">
    <h1>包装纸</h1>
    <p class="lede">切换卷材卷宽后，算纸台新单的下料长与张数会随之变化；已写入用纸档的编号仍钉住写入时的卷宽。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-else class="paper-grid">
      <div v-for="p in items" :key="p.id" class="paper-tile">
        <strong>{{ p.name }}</strong>
        <span class="meta">当前卷宽 {{ p.roll_width }} m</span>
        <div class="row" style="margin: 0.6rem 0 0">
          <input v-model="drafts[p.id]" type="number" step="0.01" min="0" aria-label="新卷宽" />
          <button :disabled="saving === p.id" @click="save(p)">改卷宽</button>
        </div>
      </div>
    </div>
  </div>
</template>
