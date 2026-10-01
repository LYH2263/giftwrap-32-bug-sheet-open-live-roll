<script setup>
// 落库快照是唯一真相：张数/卷宽只读 run.result，禁止按现行卷宽重切

import { onMounted, ref, watch } from 'vue'
import { getJSON } from '../api'
import BoxUnfold from '../components/BoxUnfold.vue'

const props = defineProps({ id: String })
const run = ref(null)
const box = ref(null)
const dry = ref(null)
const err = ref('')

async function load() {
  run.value = null
  box.value = null
  dry.value = null
  err.value = ''
  try {
    run.value = await getJSON(`/api/runs/${props.id}`)
    box.value = await getJSON(`/api/boxes/${run.value.box_id}`)
    // 同卷同盒再干算（不落库），与落库回看互证
    dry.value = await getJSON(
      `/api/estimate?box_id=${run.value.box_id}&paper_id=${run.value.result.paper_id}`,
    )
  } catch (e) {
    err.value = String(e.message || e)
  }
}

onMounted(load)
watch(() => props.id, load)
</script>

<template>
  <div class="page">
    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="run">
      <h1>用纸档 #{{ run.id }}</h1>
      <p class="lede">
        {{ run.box_name }} ｜ {{ run.result.paper_name }}
        <span class="pill">落库钉住</span>
      </p>
      <ul class="item-list">
        <li><span>用纸面积</span><span class="meta">{{ run.result.paper_m2 }} m²</span></li>
        <li><span>卷宽（写入时）</span><span class="meta">{{ run.result.roll_width }} m</span></li>
        <li><span>本次下料长</span><span class="meta">{{ run.result.sheet_len }} m（单张长按 1m）</span></li>
        <li><span>下料张数（写入时）</span><span class="meta">{{ run.result.sheets }} 张</span></li>
        <li><span>纸卷 id</span><span class="meta">{{ run.result.paper_id }}</span></li>
      </ul>
      <p class="cut-line">
        <span>回看落库：<strong>{{ run.result.sheets }}</strong> 张（卷宽 {{ run.result.roll_width }} m）</span>
        <span v-if="dry">
          同卷同盒干算：<strong>{{ dry.sheets }}</strong> 张（当前卷宽 {{ dry.roll_width }} m）
        </span>
        <span v-if="dry && dry.roll_width === run.result.roll_width" :class="dry.sheets === run.result.sheets ? 'verify-ok' : 'verify-bad'">
          {{ dry.sheets === run.result.sheets
            ? '✓ 同卷宽两路一致，互证通过'
            : '同卷宽下张数不一致，计算异常' }}
        </span>
        <span v-else-if="dry" class="meta">
          卷材事后已改卷宽（{{ run.result.roll_width }} → {{ dry.roll_width }} m）：本编号钉住写入值不重切，以落库为唯一真相；新单请去算纸台。
        </span>
      </p>
      <BoxUnfold
        v-if="box"
        :l="box.length"
        :w="box.width"
        :h="box.height"
        :paper-m2="run.result.paper_m2"
        :sheet-len="run.result.sheet_len"
      />
      <div class="row" style="margin-top: 1.25rem">
        <router-link
          class="btn"
          :to="`/bench?box=${run.box_id}&paper=${run.result.paper_id}`"
        >用同卷同盒去算纸台复核</router-link>
        <router-link class="btn ghost" to="/history">返回用纸档</router-link>
      </div>
    </template>
  </div>
</template>
