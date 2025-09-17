<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import BaseCard from '../components/BaseCard.vue'
import BaseInput from '../components/BaseInput.vue'
import BaseSelect from '../components/BaseSelect.vue'
import BaseTextarea from '../components/BaseTextarea.vue'
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
function fmtLocalYMD(d) {
  return [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-')
}
// Use local date (not UTC ISO) to avoid timezone shifting day (造成日期往前/往後一天的錯誤)
const todayStr = fmtLocalYMD(today)
const maxDateStr = fmtLocalYMD(new Date(today.getFullYear(), today.getMonth(), today.getDate()+6))

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
    const key = fmtLocalYMD(d)
    const zhWeek = ['週日','週一','週二','週三','週四','週五','週六'][d.getDay()]
    arr.push({
      key,
      label: `${d.getMonth()+1}/${d.getDate()}`,
      start: new Date(key + 'T00:00:00'), // local midnight of that day
      isToday: i===0,
      zh: zhWeek
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
  <h2 class="room-heading">教室資訊</h2>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }} <button v-if="!loading" @click="loadRoom">重試</button></p>
    <div v-if="!loading && !error && !room">找不到教室。</div>
    <div v-if="room">
      <h3>{{ room.name }}</h3>
      <p>{{ room.description || '—' }}</p>
  <h4>已申請時段（原始列表）</h4>
  <table v-if="room.bookings && room.bookings.length" class="tbl raw-list" style="font-size:12px;">
  <thead><tr><th>申請人</th><th>指導老師</th><th>類別</th><th>目的</th><th>開始</th><th>結束</th><th>狀態</th></tr></thead>
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

      <h4 class="section-title">七日概覽 (08:00-22:00)</h4>
      <!-- Desktop Horizontal Version -->
      <div class="timetable-wrapper week-desktop">
        <div class="week-row">
          <div class="day-col" v-for="d in weekDays" :key="d.key" :class="{ today: d.isToday }">
            <div class="day-head">
              <span class="label">{{ d.label }}<br><small class="dow">{{ d.zh }}</small></span>
              <span class="meta" v-if="weeklySpansByDay[d.key].length">
                <span class="badge total" :title="'總申請'">{{ weeklySpansByDay[d.key].length }}</span>
                <span class="badge approved" v-if="weeklySpansByDay[d.key].some(s=>s.booking.status==='approved')" :title="'核准'">{{ weeklySpansByDay[d.key].filter(s=>s.booking.status==='approved').length }}</span>
              </span>
              <span class="meta empty" v-else>—</span>
            </div>
            <div class="slots">
              <div class="track">
                <div class="slot-line" v-for="(slot,i) in timetableSlots" :key="'dsk-'+d.key+'-'+i"></div>
                <div v-for="span in weeklySpansByDay[d.key]" :key="'dskbk-'+span.booking.id" class="tt-booking" :class="span.booking.status" :style="{ '--start': span.startIdx, '--len': Math.max(1, span.endIdx - span.startIdx) }">
                  <span class="bk-label">{{ span.booking.user_name }}<small>{{ new Date(span.booking.start_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}-{{ new Date(span.booking.end_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}</small></span>
                </div>
              </div>
              <div class="times">
                <span v-for="(slot,i) in timetableSlots" :key="'dsk-t-'+d.key+'-'+i" v-if="i%2===0" class="t-label">{{ slot }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- Mobile / Narrow Version -->
      <div class="timetable-wrapper week-mobile">
        <div class="day-cards">
          <div class="card" v-for="d in weekDays" :key="'m-'+d.key" :class="{ today: d.isToday }">
            <div class="card-head">
              <span>{{ d.label }} <small style="display:block; font-size:10px; margin-top:2px; color:var(--text-muted);">{{ d.zh }}</small></span>
              <span class="mini-meta" v-if="weeklySpansByDay[d.key].length">{{ weeklySpansByDay[d.key].length }} / {{ weeklySpansByDay[d.key].filter(s=>s.booking.status==='approved').length }}</span>
              <span v-else class="mini-meta empty">—</span>
            </div>
            <div class="card-track">
              <div class="slot-row" v-for="(slot,i) in timetableSlots" :key="'mline-'+d.key+'-'+i"></div>
              <div v-for="span in weeklySpansByDay[d.key]" :key="'mbk-'+span.booking.id" class="tt-booking" :class="span.booking.status" :style="{ '--start': span.startIdx, '--len': Math.max(1, span.endIdx - span.startIdx) }">
                <span class="bk-label">{{ span.booking.user_name }}<small>{{ new Date(span.booking.start_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}</small></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <h4 class="section-title" style="margin-top:2rem;">申請借用</h4>
      <BaseCard class="booking-card-card">
        <div class="card-head"><span class="icon">📝</span><span class="title">借用申請表單</span></div>
        <form @submit.prevent="submit" class="form-grid enhanced">
          <BaseInput label="姓名" v-model="form.user_name" required />
          <BaseInput label="指導老師" v-model="form.user_identity" required placeholder="指導老師姓名或單位" />
          <BaseSelect label="類別" v-model="form.category">
            <option value="meeting">會議</option>
            <option value="course">課程</option>
            <option value="activity">活動</option>
          </BaseSelect>
          <BaseInput type="date" label="日期" v-model="form.date" :min="todayStr" :max="maxDateStr" required />
          <BaseSelect label="開始" v-model="form.start_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in halfHourSlots" :key="s" :value="s">{{ s }}</option>
          </BaseSelect>
          <BaseSelect label="結束" v-model="form.end_hm" required>
            <option value="" disabled>--</option>
            <option v-for="s in availableEndSlots()" :key="s" :value="s">{{ s }}</option>
          </BaseSelect>
          <BaseTextarea class="full-span" label="用途" v-model="form.purpose" rows="3" placeholder="用途說明" />
          <div class="actions full-span">
            <button type="submit" class="btn-primary btn">送出申請</button>
            <button type="button" class="btn" @click="form.user_name='';form.user_identity='';form.purpose='';form.start_hm='';form.end_hm='';submitOk='';submitError=''">清除</button>
          </div>
          <div v-if="submitError" class="alert error full-span">⚠️ {{ submitError }}</div>
          <div v-if="submitOk" class="alert ok full-span">✅ {{ submitOk }}</div>
        </form>
      </BaseCard>
    </div>
  </div>
</template>

<style scoped>
.form-grid { display:grid; gap:0.9rem; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); max-width:880px; margin-top:0.75rem; }
.form-grid.enhanced { align-items:start; }
.form-grid :deep(.base-input), .form-grid :deep(.base-select) { width:100%; }
.full-span { grid-column:1/-1; }
.actions { display:flex; gap:.75rem; }
.textarea-label textarea { width:100%; box-sizing:border-box; resize:vertical; }
.booking-card-card { background:linear-gradient(145deg,var(--surface) 0%, var(--surface-alt) 100%); position:relative; overflow:hidden; }
.booking-card-card::before { content:""; position:absolute; inset:0; pointer-events:none; background:radial-gradient(circle at 85% 15%, rgba(99,102,241,0.15), transparent 60%); }
.msg { font-size:12px; margin:0; }
.msg.error { color:var(--danger); }
.msg.ok { color:var(--success); }
.card-head { display:flex; align-items:center; gap:.5rem; font-weight:600; font-family:var(--heading-stack); letter-spacing:.5px; font-size:0.95rem; background:var(--surface-alt); padding:.55rem .85rem; border-radius:var(--radius-m); margin:-0.25rem 0 .25rem; box-shadow:inset 0 0 0 1px var(--border); }
.card-head .icon { font-size:1.1rem; }
.alert { padding:6px 10px; border-radius:var(--radius-m); font-size:12px; font-weight:500; line-height:1.3; box-shadow:var(--shadow-sm); }
.alert.error { background:var(--danger-bg); color:var(--danger); }
.alert.ok { background:var(--success-bg); color:var(--success); }
/* Timetable hour band & vertical guidelines */
.time-track { background:
  repeating-linear-gradient(
    to bottom,
    rgba(0,0,0,0.04) 0,
    rgba(0,0,0,0.04) 40px,
    transparent 40px,
    transparent 80px
  );
  position:relative;
}
.week-day-body { position:relative; }
.week-day-body::before { content:""; position:absolute; inset:0; background:linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px); background-size:100% 1px; pointer-events:none; }
.timetable-wrapper { max-width:none; }
.time-col { display:flex; flex-direction:column; font-size:10px; margin-right:4px; }
.time-cell { height:20px; line-height:20px; padding-right:4px; text-align:right; }
.slot-row { height:20px; }
.tt-booking { position:absolute; left:2px; right:2px; color:#fff; border-radius:4px; padding:2px 4px; font-size:10px; overflow:hidden; box-shadow:var(--shadow-sm); top:calc(var(--start) * 20px); height:calc(var(--len) * 20px - 2px); z-index:1; }
.bk-label small { font-size:9px; opacity:0.85; }
.raw-list { border-radius:8px !important; }
/* New dual-block timetable layout */
.week-desktop { display:block; }
.week-mobile { display:none; }
@media (max-width: 640px){ .week-desktop { display:none; } .week-mobile { display:block; } }
.week-row { display:flex; gap:8px; }
.day-col { flex:1 0 0; background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius-m); padding:4px 4px 8px; position:relative; min-width:0; }
.day-col.today { outline:2px solid var(--primary); outline-offset:2px; }
.day-col .day-head { display:flex; justify-content:space-between; align-items:center; background:var(--surface); border-radius:var(--radius-s); padding:4px 6px; font-size:12px; font-weight:600; margin-bottom:4px; box-shadow:inset 0 0 0 1px var(--border); }
.day-col .badge { font-size:10px; padding:2px 6px; border-radius:999px; line-height:1; background:var(--surface-alt); box-shadow:inset 0 0 0 1px var(--border); }
.day-col .badge.total { background:var(--info-bg); color:var(--info); }
.day-col .badge.approved { background:var(--success-bg); color:var(--success); }
.slots { position:relative; }
.track { position:relative; height:560px; background:repeating-linear-gradient(to bottom, rgba(0,0,0,0.05) 0, rgba(0,0,0,0.05) 40px, transparent 40px, transparent 80px); border-radius:6px; overflow:hidden; }
.slot-line { height:20px; }
.tt-booking { left:3px; right:3px; top:calc(var(--start)*20px); height:calc(var(--len)*20px - 3px); }
.times { margin-top:4px; display:grid; grid-template-columns:repeat(auto-fill,minmax(40px,1fr)); gap:2px; }
.t-label { font-size:10px; color:var(--text-muted); text-align:center; }
.day-cards { display:flex; gap:10px; overflow-x:auto; padding:4px 2px 8px; }
.card { flex:0 0 220px; background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius-m); padding:4px 6px 8px; position:relative; }
.card.today { outline:2px solid var(--primary); outline-offset:2px; }
.card-head { display:flex; justify-content:space-between; font-size:12px; font-weight:600; background:var(--surface); padding:4px 6px; border-radius:var(--radius-s); margin-bottom:4px; box-shadow:inset 0 0 0 1px var(--border); }
.card-track { position:relative; height:400px; background:repeating-linear-gradient(to bottom, rgba(0,0,0,0.05) 0, rgba(0,0,0,0.05) 40px, transparent 40px, transparent 80px); border-radius:6px; }
.card-track .slot-row { height:20px; }
.card .tt-booking { left:4px; right:4px; top:calc(var(--start)*20px); height:calc(var(--len)*20px - 3px); }
.mini-meta { font-size:10px; background:var(--surface-alt); padding:2px 5px; border-radius:999px; box-shadow:inset 0 0 0 1px var(--border); }
.mini-meta.empty { opacity:0.5; }
.day-head .label small.dow { font-size:10px; font-weight:500; color:var(--text-muted); }
</style>
