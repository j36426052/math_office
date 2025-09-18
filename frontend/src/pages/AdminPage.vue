<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { fetchBookings, adminUpdateBooking, adminDeleteBooking, createSemesterBookings, setAdminAuth, verifyAdmin, pingAdmin } from '../api'
import { fetchRooms } from '../api'
import StatusChip from '../components/StatusChip.vue'
import BaseButton from '../components/BaseButton.vue'
import BaseCard from '../components/BaseCard.vue'
import BaseInput from '../components/BaseInput.vue'
import BaseSelect from '../components/BaseSelect.vue'
import BaseTable from '../components/BaseTable.vue'
import { authState, markAdmin, clearAdmin } from '../auth'

const bookings = ref([])
const loading = ref(true)
const error = ref('')
const needLogin = ref(false)
const adminUser = ref('')
const adminPass = ref('')
const authError = ref('')
const filter = ref('all')

const semForm = ref({
  room_id: null, // internal id
  category: 'meeting', // meeting as default
  user_name: '',
  user_identity: '', // 指導老師
  purpose: '',
  start_date: '',
  end_date: '',
  start_hm: '08:00', // fixed start at 08:00
  end_hm: ''
})
const rooms = ref([])
const roomMap = computed(()=>{
  const m = {}
  for(const r of rooms.value) m[r.id] = r.name
  return m
})

// Table filter & sort state
const filterRoom = ref('all')
const filterStart = ref('')
const filterEnd = ref('')
const sortKey = ref('requested_at') // 'room' | 'requested_at'
const sortDir = ref('desc') // 'asc' | 'desc'

const filteredSortedBookings = computed(()=>{
  let arr = bookings.value.slice()
  // filter by room
  if(filterRoom.value !== 'all') {
    arr = arr.filter(b => String(b.room_id) === String(filterRoom.value))
  }
  // filter by date range (compare start_time date)
  if(filterStart.value) {
    const s = new Date(filterStart.value)
    arr = arr.filter(b => new Date(b.start_time) >= s)
  }
  if(filterEnd.value) {
    const e = new Date(filterEnd.value)
    // inclusive end date: use end of day
    e.setHours(23,59,59,999)
    arr = arr.filter(b => new Date(b.start_time) <= e)
  }
  // sort
  arr.sort((a,b)=>{
    let av, bv
    if(sortKey.value === 'room') {
      av = roomMap.value[a.room_id] || ''
      bv = roomMap.value[b.room_id] || ''
      if(av === bv) return a.id - b.id
      return av.localeCompare(bv)
    } else { // requested_at
      av = new Date(a.requested_at || a.created_at).getTime()
      bv = new Date(b.requested_at || b.created_at).getTime()
      if(av === bv) return a.id - b.id
      return av - bv
    }
  })
  if(sortDir.value === 'desc') arr.reverse()
  return arr
})
const semResult = ref(null)
const semError = ref('')
const semPreview = ref([])

const CATEGORY_WINDOWS = {
  activity: { start: 5, end: 22 },
  meeting: { start: 5, end: 17 },
  course: { start: 5, end: 22 }, // same as activity
}

const halfHourSlots = computed(()=>{
  const win = CATEGORY_WINDOWS[semForm.value.category] || CATEGORY_WINDOWS['activity']
  const { start, end } = win
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
  // start time fixed 08:00; filter strictly after 08:00
  return halfHourSlots.value.filter(s => s > semForm.value.start_hm)
}

function sameWeekday(d1, d2) {
  return new Date(d1).getDay() === new Date(d2).getDay()
}

function genPreview() {
  semPreview.value = []
  const f = semForm.value
  if(!f.start_date || !f.end_date || !f.start_hm || !f.end_hm) return
  if(new Date(f.end_date) < new Date(f.start_date)) return
  const start = new Date(f.start_date)
  const end = new Date(f.end_date)
  const weekday = start.getDay()
  let cur = new Date(start)
  while(cur <= end) {
    if(cur.getDay() === weekday) {
      semPreview.value.push(cur.toISOString().slice(0,10) + ' ' + f.start_hm + '-' + f.end_hm)
      cur.setDate(cur.getDate() + 7)
    } else {
      cur.setDate(cur.getDate() + 1)
    }
    if(semPreview.value.length > 120) break // safety cap
  }
}

// Watchers (simple manual re-gen)
;['start_date','end_date','start_hm','end_hm'].forEach(k=>{
  watch(()=>semForm.value[k], ()=>{ genPreview() })
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if(filter.value !== 'all') params.status = filter.value
    bookings.value = await fetchBookings(params)
  } catch (e) {
  error.value = e.message || '讀取失敗'
  } finally { loading.value = false }
}

onMounted(async ()=>{
  // detect mode first
  let ping = null
  try { ping = await pingAdmin() } catch {}
  if(ping && ping.ok && !ping.auth_enabled) {
    // open mode
    markAdmin('open')
    needLogin.value = false
    await Promise.all([load(), loadRooms()])
    return
  }
  let su = null, sp = null
  try { su = localStorage.getItem('admin_user'); sp = localStorage.getItem('admin_pass') } catch {}
  if(su && sp) {
    setAdminAuth(su, sp)
    try { await verifyAdmin(); markAdmin(su); needLogin.value = false } catch {
  try { localStorage.removeItem('admin_user'); localStorage.removeItem('admin_pass') } catch {}
  setAdminAuth(null,null); needLogin.value = true
    }
  } else {
    needLogin.value = true
  }
  await Promise.all([load(), loadRooms()])
})

async function loadRooms() {
  try { rooms.value = await fetchRooms() } catch(e) { console.warn('load rooms failed', e) }
  if(!semForm.value.room_id && rooms.value.length) semForm.value.room_id = rooms.value[0].id
}

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
  if(!f.start_date || !f.end_date || !f.end_hm) { // start_hm fixed
    semError.value = '請完整填寫日期與時間'; return
  }
  if(new Date(f.end_date) < new Date(f.start_date)) { semError.value='結束日期需晚於或等於開始日期'; return }
  if(!sameWeekday(f.start_date, f.start_date)) { semError.value='開始日期無效'; return }
  // enforce end_date same weekday lock
  if(new Date(f.start_date).getDay() !== new Date(f.end_date).getDay()) {
    semError.value = '開始與結束日期必須為同一星期幾'; return
  }
  try {
    const payload = {
      room_id: Number(f.room_id),
      category: f.category,
      user_name: f.user_name,
      user_identity: f.user_identity,
      purpose: f.purpose,
      start_date: f.start_date,
      end_date: f.end_date,
      start_time_hm: '08:00', // enforce start 08:00
      end_time_hm: f.end_hm
    }
    const res = await createSemesterBookings(payload)
    semResult.value = res
    await load()
  console.log('[semester] created', res)
  } catch(e) {
    semError.value = e.message || '建立失敗'
  console.error('[semester] error', e)
  }
}

function attemptLogin() {
  authError.value = ''
  if(!adminUser.value || !adminPass.value) { authError.value = '請輸入帳號與密碼'; return }
  setAdminAuth(adminUser.value, adminPass.value)
  verifyAdmin().then(()=>{
  try { localStorage.setItem('admin_user', adminUser.value); localStorage.setItem('admin_pass', adminPass.value) } catch {}
    markAdmin(adminUser.value)
    needLogin.value = false
    load()
  }).catch(()=>{
    authError.value = '登入失敗'
    setAdminAuth(null,null)
  })
}

function logoutAdmin() {
  try { localStorage.removeItem('admin_user'); localStorage.removeItem('admin_pass') } catch {}
  setAdminAuth(null, null)
  bookings.value = []
  needLogin.value = true
  clearAdmin()
}
</script>

<template>
  <div>
  <div v-if="needLogin && authState.authEnabled" class="login-only">
    <BaseCard class="login-panel">
      <h2 class="login-title">管理登入</h2>
      <div class="login-fields">
        <BaseInput label="帳號" v-model="adminUser" />
        <BaseInput label="密碼" type="password" v-model="adminPass" />
        <div class="login-actions"><BaseButton variant="primary" @click="attemptLogin">登入</BaseButton></div>
      </div>
      <p v-if="authError" class="err">{{ authError }}</p>
    </BaseCard>
  </div>
  <div v-else>
    <div style="display:flex; align-items:center; justify-content:space-between; gap:1rem;">
      <h2 style="margin:0;">後台管理</h2>
      <BaseButton size="sm" v-if="authState.authEnabled && authState.isAdmin" @click="logoutAdmin">登出</BaseButton>
    </div>
  <details style="margin:1rem 0;" open class="sem-wrapper">
      <summary class="sem-summary">整學期借用建立</summary>
      <form @submit.prevent="submitSemester" class="sem-grid">
        <BaseSelect label="教室" v-model="semForm.room_id" required>
          <option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option>
        </BaseSelect>
        <BaseSelect label="類別" v-model="semForm.category">
          <option value="meeting">會議</option>
          <option value="course">課程</option>
          <option value="activity">活動</option>
        </BaseSelect>
        <div>
          <label style="font-size:12px; font-weight:600; display:block; margin-bottom:4px;">週期日 (自動)</label>
          <div style="font-size:12px; padding:6px 8px; border:1px solid var(--border); border-radius:8px; background:var(--surface-alt); min-height:36px; display:flex; align-items:center;">
            <span v-if="semForm.start_date">{{ ['週日','週一','週二','週三','週四','週五','週六'][new Date(semForm.start_date).getDay()] }}</span>
            <span v-else style="opacity:.6;">選擇開始日期後顯示</span>
          </div>
        </div>
        <BaseInput label="開始日期" type="date" v-model="semForm.start_date" required />
  <BaseInput label="結束日期" type="date" v-model="semForm.end_date" required :min="semForm.start_date" />
  <BaseInput label="開始" v-model="semForm.start_hm" disabled />
        <BaseSelect label="結束" v-model="semForm.end_hm" required>
          <option value="" disabled>--</option>
          <option v-for="s in endSlots()" :key="s" :value="s">{{ s }}</option>
        </BaseSelect>
        <BaseInput label="申請人" v-model="semForm.user_name" required />
  <BaseInput label="指導老師" v-model="semForm.user_identity" required />
        <label style="grid-column:1/-1; font-size:12px; font-weight:600;">用途<textarea v-model="semForm.purpose" rows="2" style="margin-top:4px; width:100%;" /></label>
        <div style="grid-column:1/-1; display:flex; gap:.5rem;">
          <BaseButton variant="primary" type="submit">建立</BaseButton>
          <BaseButton type="button" @click="semForm.user_name='';semForm.user_identity='';semForm.purpose=''">清除文字</BaseButton>
        </div>
        <p v-if="semError" style="color:red;grid-column:1/-1;">{{ semError }}</p>
        <div v-if="semResult" class="sem-result">
          <div>建立成功筆數: {{ semResult.created_ids.length }}</div>
          <div v-if="semResult.skipped_conflicts.length">衝突略過: {{ semResult.skipped_conflicts.length }} 筆</div>
        </div>
        <div v-if="semPreview.length" class="sem-preview" style="grid-column:1/-1; font-size:11px; line-height:1.3; max-height:120px; overflow:auto; background:var(--surface); border:1px solid var(--border); padding:6px 8px; border-radius:8px;">
          <strong>預覽 ({{ semPreview.length }} 週):</strong>
          <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">
            <span v-for="p in semPreview" :key="p" style="padding:2px 6px; background:var(--surface-alt); border:1px solid var(--border); border-radius:999px;">{{ p }}</span>
          </div>
        </div>
      </form>
    </details>
    <div class="section-divider" />
    <div class="filters-combo">
      <div class="status-filter">
        <BaseSelect label="狀態篩選" v-model="filter" @change="load">
          <option value="all">全部</option>
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </BaseSelect>
      </div>
      <div class="table-filters">
        <BaseSelect label="教室" v-model="filterRoom">
          <option value="all">全部教室</option>
          <option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option>
        </BaseSelect>
        <BaseInput label="開始日" type="date" v-model="filterStart" />
        <BaseInput label="結束日" type="date" v-model="filterEnd" />
        <BaseSelect label="排序欄位" v-model="sortKey">
          <option value="requested_at">提交時間</option>
          <option value="room">教室</option>
        </BaseSelect>
        <BaseSelect label="方向" v-model="sortDir">
          <option value="desc">↓</option>
          <option value="asc">↑</option>
        </BaseSelect>
        <BaseButton size="sm" type="button" @click="filterRoom='all';filterStart='';filterEnd='';sortKey='requested_at';sortDir='desc'">重置</BaseButton>
      </div>
    </div>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }}</p>
    <BaseTable v-if="!loading && filteredSortedBookings.length" :columns="[
  {label:'ID'}, {label:'教室'}, {label:'申請人'}, {label:'指導老師'}, {label:'類別'}, {label:'用途'}, {label:'申請時間'}, {label:'開始'}, {label:'結束'}, {label:'狀態'}, {label:'操作'}
    ]">
  <tr v-for="b in filteredSortedBookings" :key="b.id">
        <td>{{ b.id }}</td>
        <td>{{ roomMap[b.room_id] || b.room_id }}</td>
        <td>{{ b.user_name }}</td>
  <td>{{ b.user_identity }}</td>
        <td>{{ b.category }}</td>
        <td>{{ b.purpose }}</td>
        <td>{{ new Date(b.requested_at || b.created_at).toLocaleString() }}</td>
        <td>{{ new Date(b.start_time).toLocaleString() }}</td>
        <td>{{ new Date(b.end_time).toLocaleString() }}</td>
        <td><StatusChip :status="b.status" /></td>
        <td style="white-space:nowrap; display:flex; gap:4px;">
          <BaseButton size="sm" variant="primary" @click="setStatus(b,'approved')" :disabled="b.status==='approved'">核可</BaseButton>
          <BaseButton size="sm" @click="setStatus(b,'rejected')" :disabled="b.status==='rejected'">退回</BaseButton>
          <BaseButton size="sm" variant="danger" @click="remove(b)">刪除</BaseButton>
        </td>
      </tr>
    </BaseTable>
  <p v-else-if="!loading">無符合資料</p>
  </div>
  </div>
</template>

<style scoped>
.sem-wrapper { background:var(--surface); border:var(--border-width) solid var(--border); border-radius:var(--radius-l); padding:.25rem .75rem .75rem; }
.sem-summary { font-weight:600; cursor:pointer; list-style:none; outline:none; }
.sem-summary::-webkit-details-marker { display:none; }
.sem-grid { display:grid; gap:.75rem; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); background:var(--surface-alt); padding:0.9rem; border:var(--border-width) solid var(--border); border-radius:var(--radius-m); }
.sem-grid input, .sem-grid select, .sem-grid textarea { width:100%; box-sizing:border-box; }
.sem-result { grid-column:1/-1; font-size:12px; background:var(--info-bg); color:var(--text); padding:.5rem; border:1px solid var(--border); border-radius:var(--radius-s); }
.err { color:red; margin:0; font-size:.85rem; }
.login-only { display:flex; justify-content:center; align-items:center; min-height:50vh; }
.login-panel { width:min(420px, 100%); padding:1rem; }
.login-title { margin:0 0 1rem; text-align:center; }
.login-fields { display:flex; flex-direction:column; gap:.75rem; margin-bottom:.5rem; }
.login-actions { display:flex; justify-content:flex-end; }
.table-filters { display:flex; flex-wrap:wrap; gap:.75rem; margin:0.5rem 0 1rem; background:var(--surface); padding:.75rem; border:1px solid var(--border); border-radius:var(--radius-m); }
.table-filters > * { flex:1 1 140px; }
.filters-combo { display:flex; flex-direction:column; gap:.75rem; margin-top:.5rem; }
.status-filter { max-width:200px; }
.section-divider { border-top:1px solid var(--border); margin:1.25rem 0; }
</style>
