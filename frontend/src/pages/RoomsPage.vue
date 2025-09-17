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
  return { date: d, label: `${d.getMonth()+1}/${d.getDate()}` }
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
    rooms.value = await fetchWeeklyRooms()
  } catch (e) {
    error.value = e.message || '讀取失敗'
  } finally { loading.value = false }
})
</script>

<template>
  <div>
  <h2 style="margin-top:0;">教室列表 / 本週(7天)預約概況</h2>
  <p class="muted text-sm">從今日開始往後 7 天。點選教室可檢視詳細並申請。</p>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }}</p>

  <table v-if="!loading && !error" class="weekly-table tbl">
      <thead>
        <tr>
          <th style="min-width:140px;">教室</th>
          <th v-for="d in days" :key="d.label">{{ d.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rooms" :key="r.id">
          <td class="room-cell">
            <router-link :to="`/rooms/${r.id}`" class="room-link">{{ r.name }}</router-link>
            <div class="desc muted" v-if="r.description">{{ r.description }}</div>
          </td>
          <td v-for="(d, idx) in days" :key="idx" class="day-cell">
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
.weekly-table { width:100%; font-size:12px; }
.room-cell { font-weight:600; font-size:13px; }
.day-cell { min-width:120px; position:relative; }
.slot-wrapper { display:flex; flex-direction:column; gap:4px; }
.booking-chip { border-radius:4px; padding:2px 4px; line-height:1.2; }
.chip-text small { display:block; font-size:10px; opacity:.8; }
.room-link { color:var(--primary); }
.room-link:hover { text-decoration:underline; }
</style>
