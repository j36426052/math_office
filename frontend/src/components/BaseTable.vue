<script setup>
const props = defineProps({ columns: { type:Array, required:true } })
</script>
<template>
  <div class="table-wrapper">
    <table class="tbl">
      <thead>
        <tr>
          <th v-for="c in columns" :key="c.key || c.label" :style="c.thStyle">{{ c.label }}</th>
        </tr>
      </thead>
      <tbody>
        <slot />
      </tbody>
    </table>
  </div>
</template>
<style scoped>
.table-wrapper { width:100%; overflow:auto; border-radius:var(--radius-l); }
</style>
