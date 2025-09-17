<template>
  <div class="base-card"><slot /></div>
</template>
<style scoped>
.base-card { background:var(--surface); border:var(--border-width) solid var(--border); border-radius:var(--radius-l); padding:1rem 1.25rem; box-shadow:var(--shadow-sm); }
</style>
