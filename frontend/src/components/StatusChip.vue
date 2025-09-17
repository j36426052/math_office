<script setup>
const props = defineProps({ status: { type: String, required: true } })
</script>

<template>
  <span class="chip" :class="status">{{ status }}</span>
</template>

<style scoped>
.chip { display:inline-block; padding:2px 8px; font-size:11px; line-height:1.2; border-radius:999px; font-weight:500; text-transform:uppercase; letter-spacing:.5px; background:var(--chip-default-bg); color:var(--chip-text); }
.chip.pending { background:var(--chip-pending-bg); }
.chip.approved { background:var(--chip-approved-bg); }
.chip.rejected { background:var(--chip-rejected-bg); text-decoration:line-through; }
</style>
