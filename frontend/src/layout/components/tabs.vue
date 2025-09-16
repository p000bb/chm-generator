<template>
  <div class="grid w-full grid-cols-3 bg-gray-700 p-1 rounded-lg">
    <template v-for="tab in tabs" :key="tab.key">
      <button
        @click="openRoute(tab.key)"
        :class="[
          'flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
          activeTab === tab.key
            ? 'bg-black text-white'
            : 'text-white hover:bg-gray-600',
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
import { ref } from "vue";
import { useRouter } from "vue-router";

const activeTab = ref("script");
const router = useRouter();

const tabs = [
  {
    name: "脚本管理",
    key: "script",
    icon: PlayCircle,
  },
  {
    name: "配置管理",
    key: "setting",
    icon: Settings,
  },
  {
    name: "运行日志",
    key: "log",
    icon: Terminal,
  },
];

const openRoute = (key: string) => {
  activeTab.value = key;
  router.push(`/${key}`);
};
</script>

<style></style>
