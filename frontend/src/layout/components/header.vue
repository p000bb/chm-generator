<template>
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-white">{{ title }}</h1>
      <p class="text-slate-400 mt-1">{{ description }}</p>
    </div>
    <div
      class="bg-green-500 text-white px-3 py-1 rounded-md text-sm font-medium"
    >
      {{ version }}
    </div>
  </div>
</template>

<script lang="ts" setup>
const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  description: {
    type: String,
    default: "",
  },
  version: {
    type: String,
    default: "",
  },
});
</script>

<style></style>
