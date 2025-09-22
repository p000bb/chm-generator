<script setup lang="ts">
import CustomTitleBar from "@/components/CustomTitleBar.vue";
</script>

<template>
  <div class="app-container">
    <CustomTitleBar />
    <div class="app-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped lang="scss">
.app-container {
  @apply h-screen flex flex-col bg-slate-900;
}

.app-content {
  @apply flex-1 overflow-auto;
}
</style>
