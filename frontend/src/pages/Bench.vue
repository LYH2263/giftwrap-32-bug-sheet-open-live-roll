<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const route = useRoute()
const boxes = ref([])
const papers = ref([])
const bid = ref(null)
const pid = ref(null)
const out = ref(null)
const err = ref('')
const busy = ref(false)

onMounted(async () => {
  try {
    boxes.value = (await getJSON('/api/boxes')).items.filter((b) => b.data_quality === 'clean')
    papers.value = (await getJSON('/api/papers')).items
    const qb = Number(route.query.box)
    const qp = Number(route.query.paper)
    bid.value = boxes.value.some((b) => b.id === qb) ? qb : (boxes.value[0]?.id ?? null)
    pid.value = papers.value.some((p) => p.id === qp) ? qp : (papers.value[0]?.id ?? null)
  } catch (e) {
    err.value = String(e.message || e)
  }
})

async function go(save) {
  err.value = ''
  if (pid.value == null) {
    err.value = '必须先选择纸卷再算纸。'
    return
  }
  busy.value = true
  try {
    const q = `box_id=${bid.value}&paper_id=${pid.value}`
    out.value = save
      ? await postJSON('/api/estimate', { box_id: bid.value, paper_id: pid.value, save: true })
      : await getJSON(`/api/estimate?${q}`)
  } catch (e) {
    out.value = null
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>算纸</h1>
    <p class="lede">先按面积试算，绑定纸卷后给出卷宽下料长与张数（单张长按 1m），确认后再写入用纸档。</p>
    <div class="row">
      <select v-model.number="bid">
        <option v-for="b in boxes" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model.number="pid">
        <option :value="null" disabled>选择纸卷…</option>
        <option v-for="p in papers" :key="p.id" :value="p.id">
          {{ p.name }}（卷宽 {{ p.roll_width }} m）
        </option>
      </select>
      <button :disabled="busy" @click="go(false)">试算</button>
      <button class="ribbon" :disabled="busy" @click="go(true)">写入用纸档</button>
    </div>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-if="out" class="result-board">
      <div class="figure">{{ out.paper_m2 }}<span>m²</span></div>
      <p class="cut-line">
        <span>纸卷：<strong>{{ out.paper_name }}</strong></span>
        <span>卷宽 <strong>{{ out.roll_width }}</strong> m</span>
        <span>本次下料长 <strong>{{ out.sheet_len }}</strong> m</span>
        <span>下料张数 <strong>{{ out.sheets }}</strong> 张</span>
      </p>
      <p class="stat-line" v-if="out.ribbon">
        十字丝带约 {{ out.ribbon.ribbon_m ?? out.ribbon }} m
      </p>
      <p v-if="out?.run_id" class="stat-line">
        已写入用纸档：<router-link :to="`/runs/${out.run_id}`">#{{ out.run_id }} 打开回看</router-link>
      </p>
      <BoxUnfold
        :l="out.box.length"
        :w="out.box.width"
        :h="out.box.height"
        :paper-m2="out.paper_m2"
        :sheet-len="out.sheet_len"
      />
    </div>
  </div>
</template>
