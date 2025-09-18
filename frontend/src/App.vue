<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { ref, onMounted } from 'vue'
import { authState, initAdminFromStorage, clearAdmin } from './auth'

const isDark = ref(false)

function applyTheme(dark) {
  const root = document.documentElement
  if(dark) root.classList.add('dark')
  else root.classList.remove('dark')
}

function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme(isDark.value)
  try { localStorage.setItem('pref-theme', isDark.value ? 'dark' : 'light') } catch {}
}

onMounted(()=>{
  let saved = null
  try { saved = localStorage.getItem('pref-theme') } catch {}
  if(saved) isDark.value = saved === 'dark'
  else if(window.matchMedia('(prefers-color-scheme: dark)').matches) isDark.value = true
  applyTheme(isDark.value)
  initAdminFromStorage()
})
</script>

<template>
  <header class="app-header">
    <h1 class="app-title">教室借用系統</h1>
  <nav class="app-nav flex gap-m nav-shell">
      <RouterLink to="/">目前狀態</RouterLink>
  <RouterLink v-if="authState.isAdmin" to="/admin">管理</RouterLink>
    </nav>
    <div style="margin-left:auto;" class="flex gap-s">
      <button class="btn" @click="toggleTheme" :aria-pressed="isDark">
        <span v-if="!isDark">🌙 深色</span>
        <span v-else>☀️ 淺色</span>
      </button>
    </div>
  </header>
  <main style="padding:1rem 1.25rem;max-width:960px;margin:0 auto;">
    <RouterView />
  </main>
</template>

<style scoped>
.app-nav a { font-size:0.85rem; }
.nav-shell { padding:4px 6px; background:var(--surface-alt); border:var(--border-width) solid var(--border); border-radius:999px; }
</style>
