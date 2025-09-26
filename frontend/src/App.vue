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
  @apply h-screen flex flex-col bg-white dark:bg-slate-900;
}

.app-content {
  @apply flex-1 overflow-auto;
}
</style>

<style>
/* 主题切换动画效果 */
:root {
  --theme-transition-duration: 0s;
}

/* 主题切换时的过渡效果 */
.theme-transitioning * {
  transition: background-color var(--theme-transition-duration)
      cubic-bezier(0.4, 0, 0.2, 1),
    border-color var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    color var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    fill var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    stroke var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    opacity var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1),
    transform var(--theme-transition-duration) cubic-bezier(0.4, 0, 0.2, 1);
}

/* 主题切换按钮的特殊动画效果 */
.theme-transitioning .theme-switcher-button {
  position: relative;
  overflow: hidden;
}

.theme-transitioning .theme-switcher-button::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(
    circle,
    rgba(59, 130, 246, 0.3) 0%,
    transparent 70%
  );
  transform: translate(-50%, -50%);
  animation: theme-ripple 0.6s ease-out;
  pointer-events: none;
  z-index: 1;
}

@keyframes theme-ripple {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

/* 确保动画不会影响性能 */
.theme-transitioning * {
  will-change: background-color, border-color, color, fill, stroke;
}
</style>
