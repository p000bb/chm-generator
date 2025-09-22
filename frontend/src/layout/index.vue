<template>
  <div class="h-full bg-slate-950 p-6 overflow-auto">
    <div class="max-w-7xl mx-auto space-y-6">
      <Header
        title="CHM文档生成工具"
        description="专业的CHM帮助文档生成解决方案"
        version="v1.0.0"
      />

      <div class="space-y-6">
        <Tabs />
      </div>

      <router-view v-slot="{ Component, route }">
        <keep-alive :include="keepAliveRoutes">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, watchEffect, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import Header from "./components/header.vue";
import Tabs from "./components/tabs.vue";

const router = useRouter();

// 根据路由配置动态生成需要缓存的组件名称列表
const keepAliveRoutes = computed(() => {
  const routes = router.getRoutes();
  const keepAliveComponents: string[] = [];

  routes.forEach((route) => {
    if (route.meta?.keepAlive && route.components?.default) {
      keepAliveComponents.push(route.name as string);
    }
  });

  return keepAliveComponents;
});
</script>

<style></style>
