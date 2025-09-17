<script setup>
const props = defineProps({ label:String, modelValue:[String,Number], type:{type:String,default:'text'}, placeholder:String, required:Boolean })
const emit = defineEmits(['update:modelValue'])
</script>
<template>
  <label class="field">
    <span v-if="label" class="lbl">{{ label }}</span>
    <input :type="type" :value="modelValue" :placeholder="placeholder" :required="required" @input="e=>emit('update:modelValue', e.target.value)" />
  </label>
</template>
<style scoped>
.field { display:flex; flex-direction:column; gap:4px; font-size:12px; }
.lbl { font-weight:600; }
input { width:100%; }
</style>
