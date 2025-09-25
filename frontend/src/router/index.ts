import { createRouter, createWebHashHistory } from "vue-router";

import Layout from "../layout/index.vue";
import type { RouteRecordRaw } from "vue-router";

// 导入页面组件

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "Index",
    component: Layout,
    redirect: "/script",
    children: [
      {
        path: "/script",
        name: "Script",
        component: () => import("../views/script/index.vue"),
        meta: {
          title: "脚本管理",
          keepAlive: true,
        },
      },
      {
        path: "/setting",
        name: "Setting",
        component: () => import("../views/setting.vue"),
        meta: {
          title: "配置管理",
          keepAlive: true,
        },
      },
      {
        path: "/log",
        name: "Log",
        component: () => import("../views/log.vue"),
        meta: {
          title: "运行日志",
          keepAlive: true,
        },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "404",
    component: () => import("../views/404.vue"),
    meta: {
      title: "页面未找到",
    },
  },
];

const router = createRouter({
  // 使用 hash 模式，适合 Electron 应用
  history: createWebHashHistory(),
  routes,
});

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title}`;
  }
  next();
});

export default router;
