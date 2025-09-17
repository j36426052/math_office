<script setup>
import { computed } from 'vue'
const props = defineProps({
  modelValue: String,
  label: String,
  rows: { type: Number, default: 3 },
  placeholder: String,
  disabled: Boolean,
  required: Boolean,
  maxlength: Number
})
const emit = defineEmits(['update:modelValue'])
const id = Math.random().toString(36).slice(2)
const innerValue = computed({
  get: ()=> props.modelValue,
  set: v => emit('update:modelValue', v)
})
</script>
<template>
  <label class="base-textarea">
    <span v-if="label" class="lbl">{{ label }}<span v-if="required" class="req">*</span></span>
    <textarea :id="id" v-model="innerValue" :rows="rows" :placeholder="placeholder" :disabled="disabled" :required="required" :maxlength="maxlength" />
  </label>
</template>
<style scoped>
.base-textarea { display:flex; flex-direction:column; gap:4px; font-size:12px; font-weight:500; color:var(--text); }
.base-textarea textarea { font:inherit; background:var(--surface); color:var(--text); border:var(--border-width) solid var(--border); border-radius:var(--radius-m); padding:6px 8px; resize:vertical; box-shadow:inset 0 1px 2px rgba(0,0,0,.04); }
.base-textarea textarea:focus { outline:2px solid var(--focus-ring); outline-offset:1px; }
.lbl { font-family:var(--font-stack); letter-spacing:.3px; }
.req { color:var(--danger); margin-left:2px; }
</style>
