<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { fetchRoom, createBooking } from '../api'

const route = useRoute()
const room = ref(null)
const loading = ref(true)
const error = ref('')
const submitError = ref('')
const submitOk = ref('')
let timeoutHandle

const CATEGORY_WINDOWS = {
  activity: { start: 8, end: 22 }, // 改成 08:00 起提供申請
  meeting: { start: 8, end: 17 }
}

// date boundaries (today .. today+6)
const today = new Date()
const todayStr = today.toISOString().slice(0,10)
const maxDateStr = new Date(today.getFullYear(), today.getMonth(), today.getDate()+6).toISOString().slice(0,10)

const form = ref({
  user_name: '',
  user_identity: '',
  purpose: '',
  category: 'activity',
  date: '',
  start_hm: '',
  end_hm: ''
})
form.value.date = todayStr

const halfHourSlots = computed(()=>{
  const { start, end } = CATEGORY_WINDOWS[form.value.category]
  const slots = []
  for (let h=start; h<=end; h++) {
    [0,30].forEach(m => {
      if (h === end && m>0) return
      const hh = String(h).padStart(2,'0')
      const mm = String(m).padStart(2,'0')
      slots.push(`${hh}:${mm}`)
    })
  }
  return slots
})

function availableEndSlots() {
  if(!form.value.start_hm) return []
  return halfHourSlots.value.filter(s => s > form.value.start_hm)
}

async function loadRoom() {
  clearTimeout(timeoutHandle)
  loading.value = true
  error.value = ''
  timeoutHandle = setTimeout(()=>{
    if (loading.value) {
      loading.value = false
      error.value = '載入逾時，請重試'
    }
  }, 10000)
  try {
    const data = await fetchRoom(route.params.id)
    room.value = data
  } catch (e) {
    error.value = e.message || '讀取失敗'
  } finally {
    clearTimeout(timeoutHandle)
    loading.value = false
  }
}

onMounted(loadRoom)
watch(() => route.params.id, loadRoom)

function buildISO(dateStr, hm) {
  const [h,m] = hm.split(':').map(Number)
  const d = new Date(dateStr + 'T00:00:00')
  d.setHours(h, m, 0, 0)
  return d.toISOString()
}

// Timetable 08:00-22:00 half-hour slots (boundaries list + final 22:00)
const timetableSlots = computed(()=>{
  const slots = []
  for (let h=8; h<22; h++) {
    for (let m of [0,30]) {
      const label = `${String(h).padStart(2,'0')}:${m===0?'00':'30'}`
      slots.push(label)
    }
  }
  slots.push('22:00')
  return slots
})

// Weekly (7 days) timetable meta
const weekDays = computed(()=>{
  const arr = []
  for(let i=0;i<7;i++){
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate()+i)
    arr.push({
      key: d.toISOString().slice(0,10),
      label: `${d.getMonth()+1}/${d.getDate()}`,
      start: new Date(d.toISOString().slice(0,10)+'T00:00:00')
    })
  }
  return arr
})

// Produce spans per day keyed by date string
const weeklySpansByDay = computed(()=>{
  const map = {}
  weekDays.value.forEach(day=>{ map[day.key] = [] })
  if(!room.value) return map
  const slotList = timetableSlots.value
  const slotIdx = Object.fromEntries(slotList.map((s,i)=>[s,i]))
  const clampLabel = (h,m)=>{
    if(h<8) return '08:00'
    if(h>22 || (h===22 && m>0)) return '22:00'
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`
  }
  weekDays.value.forEach(day=>{
    const dayStart = day.start
    const dayEnd = new Date(dayStart.getTime()+86400000)
    const bookings = room.value.bookings.filter(b=>{
      const s = new Date(b.start_time)
      const e = new Date(b.end_time)
      return e > dayStart && s < dayEnd
    })
    bookings.forEach(b=>{
      const s = new Date(b.start_time)
      const e = new Date(b.end_time)
      let startLabel = clampLabel(s.getHours(), s.getMinutes())
      let endLabel = clampLabel(e.getHours(), e.getMinutes())
      if(slotIdx[startLabel]==null || slotIdx[endLabel]==null) return
      const startIdx = slotIdx[startLabel]
      const endIdx = slotIdx[endLabel]
      if(endIdx <= startIdx) return
      map[day.key].push({ booking:b, startIdx, endIdx })
    })
  })
  return map
})

async function submit() {
  submitError.value = ''
  submitOk.value = ''
  try {
    if(!form.value.date || !form.value.start_hm || !form.value.end_hm) {
      submitError.value = '請完整選擇日期與時間'
      return
    }
    const payload = {
      room_id: Number(route.params.id),
      user_name: form.value.user_name,
      user_identity: form.value.user_identity,
      purpose: form.value.purpose,
      category: form.value.category,
      start_time: buildISO(form.value.date, form.value.start_hm),
      end_time: buildISO(form.value.date, form.value.end_hm)
    }
    const res = await createBooking(payload)
    submitOk.value = '申請已送出 (狀態: ' + res.status + ')'
    await loadRoom()
  } catch (e) {
    submitError.value = e.message || '申請失敗'
  }
}
</script>

<template>
  <div>
    <div style="margin-bottom:1rem;">
      <router-link to="/">← 返回列表</router-link>
    </div>
    <h2>教室資訊</h2>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }} <button v-if="!loading" @click="loadRoom">重試</button></p>
    <div v-if="!loading && !error && !room">找不到教室。</div>
    <div v-if="room">
      <h3>{{ room.name }}</h3>
      <p>{{ room.description || '—' }}</p>
  <h4>已申請時段（原始列表）</h4>
  <table v-if="room.bookings && room.bookings.length" class="tbl" style="font-size:12px;">
        <thead><tr><th>申請人</th><th>身份</th><th>類別</th><th>目的</th><th>開始</th><th>結束</th><th>狀態</th></tr></thead>
        <tbody>
          <tr v-for="b in room.bookings" :key="b.id">
            <td>{{ b.user_name }}</td>
            <td>{{ b.user_identity }}</td>
            <td>{{ b.category }}</td>
            <td>{{ b.purpose }}</td>
            <td>{{ new Date(b.start_time).toLocaleString() }}</td>
            <td>{{ new Date(b.end_time).toLocaleString() }}</td>
            <td>{{ b.status }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>目前沒有申請。</p>

  <h4 style="margin-top:2rem;">七日概覽 (08:00-22:00)</h4>
      <div class="timetable-wrapper">
        <div class="weekly-grid">
          <div class="time-col">
            <div v-for="slot in timetableSlots" :key="'time-'+slot" class="time-cell">{{ slot }}</div>
          </div>
          <div class="weekly-days">
            <div class="weekly-day" v-for="d in weekDays" :key="d.key">
              <div class="weekly-day-header">{{ d.label }}</div>
              <div class="weekly-day-body">
                <div class="slot-row" v-for="(slot,i) in timetableSlots" :key="'row-'+d.key+'-'+i"></div>
                <div v-for="span in weeklySpansByDay[d.key]" :key="'bk-'+span.booking.id" class="tt-booking" :class="span.booking.status"
                     :style="{ '--start': span.startIdx, '--len': Math.max(1, span.endIdx - span.startIdx) }">
                  <span class="bk-label">{{ span.booking.user_name }} ({{ span.booking.category }})<br>
                    <small>{{ new Date(span.booking.start_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }} - {{ new Date(span.booking.end_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}</small>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <h4 style="margin-top:2rem;">申請借用</h4>
  <form @submit.prevent="submit" class="form-grid">
        <label>姓名<input v-model="form.user_name" required /></label>
        <label>身份<input v-model="form.user_identity" required placeholder="學號/教師等" /></label>
        <label>類別
          <select v-model="form.category">
            <option value="activity">活動</option>
            <option value="meeting">會議</option>
          </select>
        </label>
  <label>日期<input type="date" v-model="form.date" :min="todayStr" :max="maxDateStr" required /></label>
        <label>開始
          <select v-model="form.start_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in halfHourSlots" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label>結束
          <select v-model="form.end_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in availableEndSlots()" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label style="grid-column:1/3;">用途<textarea v-model="form.purpose" rows="2" /></label>
        <div style="grid-column:1/3; display:flex; gap:.5rem;">
          <button type="submit">送出申請</button>
          <button type="button" @click="form.user_name='';form.user_identity='';form.purpose='';form.start_hm='';form.end_hm='';submitOk='';submitError=''">清除</button>
        </div>
        <p v-if="submitError" style="color:red;grid-column:1/3;">{{ submitError }}</p>
        <p v-if="submitOk" style="color:green;grid-column:1/3;">{{ submitOk }}</p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.form-grid { display:grid; gap:0.75rem; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); max-width:720px; margin-top:0.5rem; }
.form-grid input, .form-grid textarea, .form-grid select { width:100%; box-sizing:border-box; }
.timetable-wrapper { max-width:none; }
.time-col { display:flex; flex-direction:column; font-size:10px; margin-right:4px; }
.time-cell { height:20px; line-height:20px; padding-right:4px; text-align:right; }
.slot-row { height:20px; }
.tt-booking { position:absolute; left:0; right:0; margin-left:4px; color:#fff; border-radius:4px; padding:2px 4px; font-size:10px; overflow:hidden; box-shadow:var(--shadow-sm); top:calc(var(--start) * 20px); height:calc(var(--len) * 20px - 2px); }
.bk-label small { font-size:9px; opacity:0.85; }
.weekly-grid { display:flex; position:relative; }
.weekly-days { display:flex; flex:1; overflow-x:auto; }
.weekly-day { position:relative; flex:1 0 180px; }
.weekly-day:first-of-type { border-left:none; }
.weekly-day-header { position:sticky; top:0; font-size:11px; font-weight:600; padding:2px 4px; z-index:2; }
.weekly-day-body { position:relative; }
.weekly-day-body .slot-row:last-child { border-bottom:none; }
</style>
