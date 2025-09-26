<template>
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-slate-900 dark:text-white">
        {{ title }}
      </h1>
      <p class="text-slate-600 dark:text-slate-400 mt-1">{{ description }}</p>
    </div>
    <div class="flex items-center gap-4">
      <div
        class="bg-green-500 dark:bg-green-500 text-white px-3 py-1 rounded-md text-sm font-medium"
      >
        {{ version }}
      </div>
      <ThemeSwitcher />
    </div>
  </div>
</template>

<script lang="ts" setup>
import ThemeSwitcher from "@/components/ThemeSwitcher.vue";

defineProps({
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
