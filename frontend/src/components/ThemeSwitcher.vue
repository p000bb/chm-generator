<template>
  <div class="relative">
    <!-- 主题切换按钮 -->
    <button
      @click="toggleDropdown"
      class="theme-switcher-button flex items-center justify-center w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
    >
      <Sun
        v-if="currentTheme === 'light'"
        class="w-5 h-5 text-blue-500 dark:text-cyan-500"
      />
      <Moon
        v-else-if="currentTheme === 'dark'"
        class="w-5 h-5 text-blue-500 dark:text-cyan-500"
      />
      <Monitor v-else class="w-5 h-5 text-blue-500 dark:text-cyan-500" />
    </button>

    <!-- 下拉菜单 -->
    <div
      v-if="isDropdownOpen"
      class="absolute right-0 top-full mt-2 w-28 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50"
    >
      <div class="py-1">
        <!-- 明亮主题 -->
        <button
          @click="setTheme('light')"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          :class="{
            'text-blue-600 dark:text-cyan-400 bg-blue-50 dark:bg-slate-700':
              currentTheme === 'light',
            'text-slate-600 dark:text-slate-400': currentTheme !== 'light',
          }"
        >
          <Sun
            class="w-4 h-4"
            :class="
              currentTheme === 'light'
                ? 'text-blue-600 dark:text-cyan-400'
                : 'text-slate-500 dark:text-slate-500'
            "
          />
          <span>明亮</span>
        </button>

        <!-- 暗黑主题 -->
        <button
          @click="setTheme('dark')"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          :class="{
            'text-blue-600 dark:text-cyan-400 bg-blue-50 dark:bg-slate-700':
              currentTheme === 'dark',
            'text-slate-600 dark:text-slate-400': currentTheme !== 'dark',
          }"
        >
          <Moon
            class="w-4 h-4"
            :class="
              currentTheme === 'dark'
                ? 'text-blue-600 dark:text-cyan-400'
                : 'text-slate-500 dark:text-slate-500'
            "
          />
          <span>暗黑</span>
        </button>

        <!-- 系统主题 -->
        <button
          @click="setTheme('system')"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          :class="{
            'text-blue-600 dark:text-cyan-400 bg-blue-50 dark:bg-slate-700':
              currentTheme === 'system',
            'text-slate-600 dark:text-slate-400': currentTheme !== 'system',
          }"
        >
          <Monitor
            class="w-4 h-4"
            :class="
              currentTheme === 'system'
                ? 'text-blue-600 dark:text-cyan-400'
                : 'text-slate-500 dark:text-slate-500'
            "
          />
          <span>系统</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { Sun, Moon, Monitor } from "lucide-vue-next";
import { getStoredTheme, setStoredTheme, type Theme } from "@/utils/storage";

const currentTheme = ref<Theme>("system");
const isDropdownOpen = ref(false);

// 设置主题
const setTheme = (theme: Theme) => {
  // 添加主题切换动画
  document.documentElement.style.setProperty(
    "--theme-transition-duration",
    "0.4s"
  );
  document.documentElement.classList.add("theme-transitioning");

  // 延迟应用主题，让动画有时间开始
  setTimeout(() => {
    currentTheme.value = theme;
    isDropdownOpen.value = false;

    // 保存到localStorage
    setStoredTheme(theme);

    // 应用主题
    applyTheme(theme);

    // 动画结束后移除过渡类
    setTimeout(() => {
      document.documentElement.classList.remove("theme-transitioning");
      document.documentElement.style.removeProperty(
        "--theme-transition-duration"
      );
    }, 400);
  }, 50);
};

// 应用主题
const applyTheme = (theme: Theme) => {
  const html = document.documentElement;

  if (theme === "system") {
    // 系统主题：根据系统偏好设置
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    if (prefersDark) {
      html.classList.add("dark");
    } else {
      html.classList.remove("dark");
    }
  } else if (theme === "dark") {
    html.classList.add("dark");
  } else {
    html.classList.remove("dark");
  }
};

// 切换下拉菜单
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
};

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest(".relative")) {
    isDropdownOpen.value = false;
  }
};

// 监听系统主题变化
const handleSystemThemeChange = (e: MediaQueryListEvent) => {
  if (currentTheme.value === "system") {
    if (e.matches) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }
};

onMounted(() => {
  // 从localStorage读取保存的主题
  currentTheme.value = getStoredTheme();

  // 应用初始主题
  applyTheme(currentTheme.value);

  // 监听系统主题变化
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.addEventListener("change", handleSystemThemeChange);

  // 监听点击外部事件
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  // 清理事件监听
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.removeEventListener("change", handleSystemThemeChange);
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped></style>
