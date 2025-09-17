<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchBookings, adminUpdateBooking, adminDeleteBooking, createSemesterBookings } from '../api'

const bookings = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('all')

const semForm = ref({
  room_id: 1,
  category: 'activity',
  user_name: '',
  user_identity: '',
  purpose: '',
  weekday: 0,
  start_date: '',
  end_date: '',
  start_hm: '',
  end_hm: ''
})
const semResult = ref(null)
const semError = ref('')

const CATEGORY_WINDOWS = {
  activity: { start: 5, end: 22 },
  meeting: { start: 5, end: 17 }
}

const halfHourSlots = computed(()=>{
  const { start, end } = CATEGORY_WINDOWS[semForm.value.category]
  const arr = []
  for(let h=start; h<=end; h++) {
    for (let m of [0,30]) {
      if (h===end && m>0) continue
      arr.push(`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`)
    }
  }
  return arr
})

function endSlots() {
  if(!semForm.value.start_hm) return []
  return halfHourSlots.value.filter(s => s > semForm.value.start_hm)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if(filter.value !== 'all') params.status = filter.value
    bookings.value = await fetchBookings(params)
  } catch (e) { error.value = e.message || '讀取失敗' } finally { loading.value = false }
}

onMounted(load)

async function setStatus(b, status) {
  try { await adminUpdateBooking(b.id, status); await load() } catch(e) { alert(e.message) }
}
async function remove(b) {
  if(!confirm('確定刪除?')) return
  try { await adminDeleteBooking(b.id); await load() } catch(e) { alert(e.message) }
}

async function submitSemester() {
  semError.value = ''
  semResult.value = null
  const f = semForm.value
  if(!f.start_date || !f.end_date || !f.start_hm || !f.end_hm) {
    semError.value = '請完整填寫日期與時間'; return
  }
  try {
    const payload = {
      room_id: Number(f.room_id),
      category: f.category,
      user_name: f.user_name,
      user_identity: f.user_identity,
      purpose: f.purpose,
      weekday: Number(f.weekday),
      start_date: f.start_date,
      end_date: f.end_date,
      start_time_hm: f.start_hm,
      end_time_hm: f.end_hm
    }
    const res = await createSemesterBookings(payload)
    semResult.value = res
    await load()
  } catch(e) {
    semError.value = e.message || '建立失敗'
  }
}
</script>

<template>
  <div>
  <h2 style="margin-top:0;">後台管理 (暫無登入)</h2>
    <div style="margin:0.5rem 0;">
      <label>狀態篩選: 
        <select v-model="filter" @change="load">
          <option value="all">全部</option>
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </label>
    </div>

    <details style="margin:1rem 0;" open class="sem-wrapper">
      <summary class="sem-summary">整學期借用建立</summary>
      <form @submit.prevent="submitSemester" class="sem-grid">
        <label>教室ID<input type="number" v-model="semForm.room_id" min="1" required /></label>
        <label>類別
          <select v-model="semForm.category">
            <option value="activity">活動</option>
            <option value="meeting">會議</option>
          </select>
        </label>
        <label>星期
          <select v-model="semForm.weekday">
            <option v-for="(d,i) in ['一','二','三','四','五','六','日']" :key="i" :value="i">週{{ d }}</option>
          </select>
        </label>
        <label>開始日期<input type="date" v-model="semForm.start_date" required /></label>
        <label>結束日期<input type="date" v-model="semForm.end_date" required /></label>
        <label>開始
          <select v-model="semForm.start_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in halfHourSlots" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label>結束
          <select v-model="semForm.end_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in endSlots()" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label>申請人<input v-model="semForm.user_name" required /></label>
        <label>身份<input v-model="semForm.user_identity" required /></label>
        <label style="grid-column:1/-1;">用途<textarea v-model="semForm.purpose" rows="2" /></label>
        <div style="grid-column:1/-1; display:flex; gap:.5rem;">
          <button type="submit">建立</button>
          <button type="button" @click="semForm.user_name='';semForm.user_identity='';semForm.purpose=''">清除文字</button>
        </div>
        <p v-if="semError" style="color:red;grid-column:1/-1;">{{ semError }}</p>
  <div v-if="semResult" class="sem-result">
          <div>建立成功筆數: {{ semResult.created_ids.length }}</div>
          <div v-if="semResult.skipped_conflicts.length">衝突略過: {{ semResult.skipped_conflicts.length }} 筆</div>
        </div>
      </form>
    </details>

    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }}</p>
    <table v-if="!loading && bookings.length" class="tbl">
      <thead><tr><th>ID</th><th>教室</th><th>申請人</th><th>身份</th><th>類別</th><th>用途</th><th>申請時間</th><th>開始</th><th>結束</th><th>狀態</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="b in bookings" :key="b.id">
          <td>{{ b.id }}</td>
          <td>{{ b.room_id }}</td>
          <td>{{ b.user_name }}</td>
          <td>{{ b.user_identity }}</td>
          <td>{{ b.category }}</td>
          <td>{{ b.purpose }}</td>
          <td>{{ new Date(b.requested_at || b.created_at).toLocaleString() }}</td>
          <td>{{ new Date(b.start_time).toLocaleString() }}</td>
          <td>{{ new Date(b.end_time).toLocaleString() }}</td>
          <td>{{ b.status }}</td>
          <td style="white-space:nowrap;">
            <button class="btn" @click="setStatus(b,'approved')" :disabled="b.status==='approved'">核可</button>
            <button class="btn" @click="setStatus(b,'rejected')" :disabled="b.status==='rejected'">退回</button>
            <button class="btn btn-danger" @click="remove(b)">刪除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">無資料</p>
  </div>
</template>

<style scoped>
.tbl { border-collapse:collapse; width:100%; font-size:12px; background:var(--surface); }
.tbl th, .tbl td { border:1px solid var(--border); padding:4px 6px; }
.tbl th { background:var(--surface-alt); }
.sem-wrapper { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-m); padding:.25rem .75rem .75rem; }
.sem-summary { font-weight:600; cursor:pointer; list-style:none; outline:none; }
.sem-summary::-webkit-details-marker { display:none; }
.sem-grid { display:grid; gap:.75rem; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); background:var(--surface-alt); padding:0.75rem; border:1px solid var(--border); border-radius:var(--radius-s); }
.sem-grid input, .sem-grid select, .sem-grid textarea { width:100%; box-sizing:border-box; }
.sem-result { grid-column:1/-1; font-size:12px; background:var(--info-bg); color:var(--text); padding:.5rem; border:1px solid var(--border); border-radius:var(--radius-s); }
</style>
