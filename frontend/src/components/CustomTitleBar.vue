<template>
  <div class="custom-titlebar">
    <div class="titlebar-content">
      <div class="titlebar-drag-region">
        <div class="titlebar-icon">
          <img src="/icon.ico" alt="App Icon" class="w-4 h-4" />
        </div>
        <div class="titlebar-title">CHM文档生成工具</div>
      </div>
      <div class="titlebar-controls">
        <button @click="minimizeWindow" class="titlebar-button minimize-button">
          <Minus class="w-5 h-5" />
        </button>
        <button @click="maximizeWindow" class="titlebar-button maximize-button">
          <Square v-if="!isMaximized" class="w-4 h-4" />
          <img
            v-else
            src="/max.svg"
            alt="Restore"
            class="w-3 h-3 restore-icon"
          />
        </button>
        <button @click="closeWindow" class="titlebar-button close-button">
          <X class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Minus, Square, X } from "lucide-vue-next";
import { ref, onMounted, onUnmounted } from "vue";

const isMaximized = ref(false);

const minimizeWindow = () => {
  if (window.electronAPI) {
    window.electronAPI?.minimizeWindow();
  }
};

const maximizeWindow = () => {
  if (window.electronAPI) {
    window.electronAPI.maximizeWindow();
  }
};

const closeWindow = () => {
  if (window.electronAPI) {
    window.electronAPI.closeWindow();
  }
};

// 监听窗口状态变化
const handleWindowStateChange = (state: any) => {
  isMaximized.value = state.isMaximized;
};

onMounted(() => {
  // 初始获取窗口状态
  if (window.electronAPI) {
    window.electronAPI.getWindowState().then((state: any) => {
      isMaximized.value = state.isMaximized;
    });

    // 监听窗口状态变化事件
    window.electronAPI.onWindowStateChange(handleWindowStateChange);
  }
});

onUnmounted(() => {
  // 清理事件监听
  if (window.electronAPI) {
    window.electronAPI.offWindowStateChange(handleWindowStateChange);
  }
});
</script>

<style scoped>
.custom-titlebar {
  @apply bg-slate-800 border-b border-slate-700;
  height: 30px;
  -webkit-app-region: drag;
  user-select: none;
}

.titlebar-content {
  @apply flex items-center justify-between h-full px-2;
}

.titlebar-drag-region {
  @apply flex items-center gap-2 flex-1;
  -webkit-app-region: drag;
}

.titlebar-icon {
  @apply flex items-center;
}

.titlebar-title {
  @apply text-sm text-slate-200 font-medium;
}

.titlebar-controls {
  @apply flex items-center;
  -webkit-app-region: no-drag;
}

.titlebar-button {
  @apply w-12 h-10 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors;
  border: none;
  background: none;
  cursor: pointer;
}

.titlebar-button:hover {
  @apply bg-slate-700;
}

.close-button:hover {
  @apply bg-red-600 text-white;
}

.minimize-button:hover {
  @apply bg-slate-600;
}

.maximize-button:hover {
  @apply bg-slate-600;
}

/* 还原图标样式 */
.restore-icon {
  filter: brightness(0) saturate(100%) invert(100%) sepia(0%) saturate(0%)
    hue-rotate(0deg) brightness(100%) contrast(100%);
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.restore-icon:hover {
  opacity: 1;
}
</style>
