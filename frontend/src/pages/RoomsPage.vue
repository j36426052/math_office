<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchWeeklyRooms } from '../api'

const rooms = ref([])
const loading = ref(true)
const error = ref('')
const now = new Date()
// Start of today (local)
const startDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
const days = [...Array(7)].map((_,i)=>{
  const d = new Date(startDay.getTime() + i*86400000)
  const zhWeek = ['週日','週一','週二','週三','週四','週五','週六'][d.getDay()]
  return { date: d, label: `${d.getMonth()+1}/${d.getDate()}`, zh: zhWeek }
})

function bookingSpans(bks) {
  // Return array per booking with day index coverage
  return bks.map(b => {
    const s = new Date(b.start_time)
    const e = new Date(b.end_time)
    const indices = []
    days.forEach((d,idx)=>{
      const dayStart = d.date
      const dayEnd = new Date(dayStart.getTime()+86400000)
      if (e > dayStart && s < dayEnd) indices.push(idx)
    })
    return { booking: b, indices }
  })
}

onMounted(async () => {
  try {
    const data = await fetchWeeklyRooms()
    console.log('[RoomsPage] fetched weekly rooms raw:', data)
    if (!Array.isArray(data)) {
      console.error('[RoomsPage] data is not array', data)
      error.value = '資料格式錯誤'
      return
    }
    rooms.value = data
    console.log('[RoomsPage] rooms count', rooms.value.length, rooms.value.map(r=>r.name))
    if (rooms.value.length === 0) {
      console.warn('[RoomsPage] rooms array empty')
    }
  } catch (e) {
    error.value = e.message || '讀取失敗'
    console.error('[RoomsPage] fetch error', e)
  } finally { loading.value = false }
})
</script>

<template>
  <div>
  <h2 class="rooms-heading">教室列表 · 本週 7 天概況</h2>
  <p class="muted text-sm" style="text-align:center; margin-top:-4px;">從今日起往後 7 天 · 點選教室可檢視詳細與申請</p>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }}</p>

  <table v-if="!loading && !error" class="weekly-table tbl weekly-compact rooms-week">
      <thead>
        <tr>
          <th style="min-width:160px;">教室</th>
          <th v-for="(d,di) in days" :key="d.label" class="day-head" :class="{ 'today-col': di===0 }">{{ d.label }}<br><small style="font-weight:500; color:var(--text-muted);">{{ d.zh }}</small></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rooms" :key="r.id">
          <td class="room-cell">
            <router-link :to="`/rooms/${r.id}`" class="room-link room-pill">{{ r.name }}</router-link>
          </td>
          <td v-for="(d, idx) in days" :key="idx" class="day-cell center" :class="{ 'today-col': idx===0 }">
            <div class="slot-wrapper">
              <template v-for="(bwrap,i) in bookingSpans(r.bookings)" :key="i">
                <div v-if="bwrap.indices.includes(idx)" class="booking-chip shadow-sm" :class="bwrap.booking.status">
                  <span class="chip-text">{{ bwrap.booking.user_name }}<small>{{ new Date(bwrap.booking.start_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}-{{ new Date(bwrap.booking.end_time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) }}</small></span>
                </div>
              </template>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.rooms-heading { margin-top:0; text-align:center; font-size:1.15rem; letter-spacing:.5px; }
.weekly-table { width:100%; font-size:12px; }
.weekly-compact th, .weekly-compact td { text-align:center; }
.room-cell { font-weight:600; font-size:13px; text-align:center; }
.day-cell { min-width:110px; position:relative; }
.day-cell.center { text-align:center; }
.day-head { font-weight:600; font-size:11px; letter-spacing:.5px; }
.day-head small { font-size:10px; display:block; margin-top:2px; }
.slot-wrapper { display:flex; flex-direction:column; gap:4px; align-items:center; }
.booking-chip { border-radius:12px; padding:2px 6px; line-height:1.15; font-size:10px; font-weight:500; }
.chip-text { display:flex; flex-direction:column; align-items:center; }
.chip-text small { display:block; font-size:9px; opacity:.8; margin-top:1px; }
.room-link { color:var(--primary); display:inline-flex; justify-content:center; align-items:center; padding:6px 14px; min-width:150px; min-height:38px; border:1px solid var(--border); border-radius:14px; background:var(--surface-alt); font-size:12px; font-weight:500; letter-spacing:.3px; box-shadow:var(--shadow-sm); position:relative; }
.room-link:hover { background:var(--primary); color:var(--primary-fg); border-color:var(--primary); text-decoration:none; }
.room-link.room-pill { font-family:var(--heading-stack); }
.room-link::after { content:""; position:absolute; inset:0; border-radius:inherit; box-shadow:inset 0 0 0 1px rgba(255,255,255,0.5); pointer-events:none; }
</style>
