<script setup>
const props = defineProps({
  variant: { type: String, default: 'default' },
  size: { type: String, default: 'md' },
  disabled: { type: Boolean, default: false }
})
</script>
<template>
  <button :disabled="disabled" class="base-btn" :class="[variant, size]">
    <slot />
  </button>
</template>
<style scoped>
.base-btn { cursor:pointer; border:var(--border-width) solid var(--border); background:var(--surface-alt); color:var(--text); padding:0.55rem 1rem; font-size:0.85rem; border-radius:var(--radius-m); line-height:1.1; display:inline-flex; align-items:center; gap:0.45rem; transition:var(--transition); font-weight:500; }
.base-btn:hover:not(:disabled) { background:var(--primary); color:var(--primary-fg); border-color:var(--primary); }
.base-btn.primary { background:var(--primary); color:var(--primary-fg); border-color:var(--primary); }
.base-btn.primary:hover:not(:disabled) { background:var(--primary-hover); }
.base-btn.danger { background:var(--danger); color:#fff; border-color:var(--danger); }
.base-btn.danger:hover:not(:disabled) { filter:brightness(1.1); }
.base-btn.sm { padding:0.4rem 0.75rem; font-size:0.75rem; }
.base-btn.lg { padding:0.7rem 1.25rem; font-size:0.95rem; }
.base-btn:disabled { opacity:0.55; cursor:not-allowed; }
</style>
