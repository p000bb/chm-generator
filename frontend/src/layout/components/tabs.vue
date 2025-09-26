<template>
  <div
    class="grid w-full grid-cols-3 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg"
  >
    <template v-for="tab in tabs" :key="tab.key">
      <button
        @click="openRoute(tab.key)"
        :class="[
          'flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
          activeTab === tab.key
            ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white'
            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700',
        ]"
      >
        <component :is="tab.icon" class="h-4 w-4" />
        {{ tab.name }}
      </button>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { PlayCircle, Settings, Terminal } from "lucide-vue-next";
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

const activeTab = ref(route.name as string);

const tabs = [
  {
    name: "脚本管理",
    key: "Script",
    icon: PlayCircle,
  },
  {
    name: "配置管理",
    key: "Setting",
    icon: Settings,
  },
  {
    name: "运行日志",
    key: "Log",
    icon: Terminal,
  },
];

const openRoute = (key: string) => {
  activeTab.value = key;
  router.push({ name: key });
};

// 监听路由变化，更新 activeTab
watch(
  () => route.name,
  (newName) => {
    if (newName) {
      activeTab.value = newName as string;
    }
  }
);
</script>

<style></style>
