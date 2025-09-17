<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchBookings, adminUpdateBooking, adminDeleteBooking, createSemesterBookings, setAdminAuth, verifyAdmin, pingAdmin } from '../api'
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
  } catch (e) {
    if (e.message && e.message.toLowerCase().includes('unauthorized')) {
      needLogin.value = true
    } else {
      error.value = e.message || '讀取失敗'
    }
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
    await load()
    return
  }
  const su = localStorage.getItem('admin_user')
  const sp = localStorage.getItem('admin_pass')
  if(su && sp) {
    setAdminAuth(su, sp)
    try { await verifyAdmin(); markAdmin(su); needLogin.value = false } catch {
      localStorage.removeItem('admin_user'); localStorage.removeItem('admin_pass'); setAdminAuth(null,null); needLogin.value = true
    }
  } else {
    needLogin.value = true
  }
  await load()
})

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

function attemptLogin() {
  authError.value = ''
  if(!adminUser.value || !adminPass.value) { authError.value = '請輸入帳號與密碼'; return }
  setAdminAuth(adminUser.value, adminPass.value)
  verifyAdmin().then(()=>{
    localStorage.setItem('admin_user', adminUser.value)
    localStorage.setItem('admin_pass', adminPass.value)
    markAdmin(adminUser.value)
    needLogin.value = false
    load()
  }).catch(()=>{
    authError.value = '登入失敗'
    setAdminAuth(null,null)
  })
}

function logoutAdmin() {
  localStorage.removeItem('admin_user')
  localStorage.removeItem('admin_pass')
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
      <h2 style="margin:0 0 1rem;">管理登入</h2>
      <div class="login-fields">
        <BaseInput label="帳號" v-model="adminUser" />
        <BaseInput label="密碼" type="password" v-model="adminPass" />
        <BaseButton variant="primary" @click="attemptLogin">登入</BaseButton>
      </div>
      <p v-if="authError" class="err">{{ authError }}</p>
    </BaseCard>
  </div>
  <div v-else>
    <div style="display:flex; align-items:center; justify-content:space-between; gap:1rem;">
      <h2 style="margin:0;">後台管理</h2>
      <BaseButton v-if="authState.authEnabled" size="sm" @click="logoutAdmin">登出</BaseButton>
    </div>
    <div style="margin:0.5rem 0; max-width:200px;">
      <BaseSelect label="狀態篩選" v-model="filter" @change="load">
        <option value="all">全部</option>
        <option value="pending">pending</option>
        <option value="approved">approved</option>
        <option value="rejected">rejected</option>
      </BaseSelect>
    </div>
    <details style="margin:1rem 0;" open class="sem-wrapper">
      <summary class="sem-summary">整學期借用建立</summary>
      <form @submit.prevent="submitSemester" class="sem-grid">
        <BaseInput label="教室ID" type="number" v-model="semForm.room_id" required />
        <BaseSelect label="類別" v-model="semForm.category">
          <option value="activity">活動</option>
          <option value="meeting">會議</option>
        </BaseSelect>
        <BaseSelect label="星期" v-model="semForm.weekday">
          <option v-for="(d,i) in ['一','二','三','四','五','六','日']" :key="i" :value="i">週{{ d }}</option>
        </BaseSelect>
        <BaseInput label="開始日期" type="date" v-model="semForm.start_date" required />
        <BaseInput label="結束日期" type="date" v-model="semForm.end_date" required />
        <BaseSelect label="開始" v-model="semForm.start_hm" required>
          <option value="" disabled>--</option>
          <option v-for="s in halfHourSlots" :key="s" :value="s">{{ s }}</option>
        </BaseSelect>
        <BaseSelect label="結束" v-model="semForm.end_hm" required>
          <option value="" disabled>--</option>
          <option v-for="s in endSlots()" :key="s" :value="s">{{ s }}</option>
        </BaseSelect>
        <BaseInput label="申請人" v-model="semForm.user_name" required />
        <BaseInput label="身份" v-model="semForm.user_identity" required />
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
      </form>
    </details>
    <p v-if="loading">載入中...</p>
    <p v-if="error" style="color:red">{{ error }}</p>
    <BaseTable v-if="!loading && bookings.length" :columns="[
      {label:'ID'}, {label:'教室'}, {label:'申請人'}, {label:'身份'}, {label:'類別'}, {label:'用途'}, {label:'申請時間'}, {label:'開始'}, {label:'結束'}, {label:'狀態'}, {label:'操作'}
    ]">
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
        <td><StatusChip :status="b.status" /></td>
        <td style="white-space:nowrap; display:flex; gap:4px;">
          <BaseButton size="sm" variant="primary" @click="setStatus(b,'approved')" :disabled="b.status==='approved'">核可</BaseButton>
          <BaseButton size="sm" @click="setStatus(b,'rejected')" :disabled="b.status==='rejected'">退回</BaseButton>
          <BaseButton size="sm" variant="danger" @click="remove(b)">刪除</BaseButton>
        </td>
      </tr>
    </BaseTable>
    <p v-else-if="!loading">無資料</p>
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
.login-only { display:flex; justify-content:center; padding:2rem 0; }
.login-panel { width: min(420px, 100%); }
.login-fields { display:flex; flex-direction:column; gap:.75rem; margin-bottom:1rem; }
.login-fields input { width:100%; }
.err { color:red; margin:0; font-size:.85rem; }
</style>
