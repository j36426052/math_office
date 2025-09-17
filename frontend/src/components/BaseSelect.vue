<script setup>
const props = defineProps({ label:String, modelValue:[String,Number], required:Boolean })
const emit = defineEmits(['update:modelValue'])
</script>
<template>
  <label class="field">
    <span v-if="label" class="lbl">{{ label }}</span>
    <select :value="modelValue" :required="required" @change="e=>emit('update:modelValue', e.target.value)">
      <slot />
    </select>
  </label>
</template>
<style scoped>
.field { display:flex; flex-direction:column; gap:4px; font-size:12px; }
.lbl { font-weight:600; }
select { width:100%; }
</style>
