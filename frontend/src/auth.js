import { reactive } from 'vue'
import { setAdminAuth, verifyAdmin, pingAdmin } from './api'

export const authState = reactive({ isAdmin: false, user: null, authEnabled: true })

export async function initAdminFromStorage() {
  const u = localStorage.getItem('admin_user')
  const p = localStorage.getItem('admin_pass')
  try {
    const ping = await pingAdmin().catch(()=>null)
    if(ping && ping.ok) {
      authState.authEnabled = ping.auth_enabled
      // if auth not enabled -> treat everyone as admin (open mode)
      if(!ping.auth_enabled) {
        authState.isAdmin = true
        authState.user = 'open'
        return
      }
    }
  } catch {}
  if(u && p && authState.authEnabled) {
    setAdminAuth(u,p)
    try {
      await verifyAdmin()
      authState.isAdmin = true
      authState.user = u
    } catch {
      // invalid now -> clear
      setAdminAuth(null, null)
      localStorage.removeItem('admin_user')
      localStorage.removeItem('admin_pass')
    }
  }
}

export function markAdmin(u) {
  authState.isAdmin = true
  authState.user = u
}

export function clearAdmin() {
  authState.isAdmin = false
  authState.user = null
  authState.authEnabled = true
  setAdminAuth(null,null)
}
