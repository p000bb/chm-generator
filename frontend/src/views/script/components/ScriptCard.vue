<template>
  <div @click="handleCardClick" :class="getCardClass()">
    <div class="p-4">
      <div>
        <div class="flex items-center gap-3">
          <input
            type="checkbox"
            :checked="script.checked"
            @change="handleCardClick"
            :disabled="props.isRunning"
            class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 rounded focus:ring-blue-500 focus:ring-2 pointer-events-none"
          />
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <h4 class="text-base font-semibold text-white">
                {{ script.name }}
              </h4>
              <!-- 状态图标 -->
              <div class="flex items-center">
                <component
                  :is="getStatusIcon().component"
                  :class="getStatusIcon().class"
                />
              </div>
            </div>

            <p class="text-sm text-slate-400 mt-1">
              {{ script.description }}
            </p>
            <div class="flex items-center justify-between">
              <!-- 显示包含的脚本数量（仅组合脚本显示） -->
              <div v-if="showScriptCount" class="mt-2 text-xs text-slate-500">
                包含 {{ script.scripts?.length || 0 }} 个脚本
              </div>
              <!-- 显示预计耗时 -->
              <div v-if="script.time" class="mt-2 text-xs text-slate-500">
                预计耗时: {{ script.time }} 分钟
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 设置和帮助按钮 -->
      <div
        class="mt-3 pt-3 border-t border-slate-600 group-hover:border-slate-500 transition-colors"
      >
        <div class="flex items-center justify-end gap-2">
          <!-- 设置按钮 -->
          <!-- <button
            @click.stop="handleSettings"
            :disabled="props.isRunning"
            :class="getSettingsButtonClass()"
            title="脚本设置"
          >
            <Settings class="h-3.5 w-3.5" />
            设置
          </button> -->
          <!-- 帮助按钮 -->
          <button
            @click.stop="handleHelp"
            :class="helpButtonClass"
            title="脚本说明"
          >
            <HelpCircle class="h-3.5 w-3.5" />
            说明
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { CheckCircle2, Loader2, Circle, HelpCircle } from "lucide-vue-next";

// 定义 props
interface Props {
  script: {
    id: string;
    name: string;
    description: string;
    checked: boolean;
    status: string;
    scripts?: string[]; // 组合脚本才有此字段
    time?: number;
  };
  isRunning?: boolean;
  currentScriptIndex?: number;
  isCurrentExecuting?: boolean; // 是否是当前正在执行的脚本
  scriptResults?: Record<
    string,
    {
      success: boolean;
      output: string;
      error?: string;
      code: number;
      subScripts?: Array<{
        name: string;
        success: boolean;
        output: string;
        error?: string;
        code: number;
      }>;
    }
  >;
  showScriptCount?: boolean; // 是否显示脚本数量
}

const props = withDefaults(defineProps<Props>(), {
  isRunning: false,
  currentScriptIndex: -1,
  isCurrentExecuting: false,
  scriptResults: () => ({}),
  showScriptCount: false,
});

// 定义 emits
const emit = defineEmits<{
  toggle: [id: string];
  settings: [id: string];
  help: [id: string];
}>();

// 计算脚本状态
const getScriptStatus = (): "idle" | "running" | "completed" | "error" => {
  // 如果这个脚本是当前正在执行的脚本，则显示为运行状态
  if (props.isCurrentExecuting) {
    return "running";
  }

  // 根据脚本类型确定正确的 key
  const scriptKey = props.showScriptCount
    ? `group_${props.script.id}` // 组合脚本使用 group_ 前缀
    : `single_${props.script.id}`; // 单独脚本使用 single_ 前缀

  // 如果脚本已经执行完成
  if (props.scriptResults[scriptKey]) {
    const result = props.scriptResults[scriptKey];

    // 如果是组合脚本，检查是否有子脚本结果
    if (result.subScripts && result.subScripts.length > 0) {
      // 组合脚本：检查所有子脚本是否都完成且都成功
      const allSubScriptsCompleted = result.subScripts.every(
        (sub: any) => sub.success !== undefined
      );
      const allSubScriptsSuccess = result.subScripts.every(
        (sub: any) => sub.success
      );

      // 只有当所有子脚本都完成时才显示最终状态
      if (allSubScriptsCompleted) {
        return allSubScriptsSuccess ? "completed" : "error";
      } else {
        // 部分子脚本还在执行中，显示运行状态
        return "running";
      }
    } else {
      // 单独脚本：直接检查成功状态
      return result.success ? "completed" : "error";
    }
  }

  // 默认状态
  return "idle";
};

// 计算卡片样式
const getCardClass = () => {
  const baseClass =
    "bg-slate-900 border rounded-lg relative transition-all duration-300 group";
  const status = getScriptStatus();

  if (status === "running") {
    return `${baseClass} border-blue-500 cursor-not-allowed running-card`;
  } else if (props.isRunning) {
    return `${baseClass} border-slate-800 cursor-not-allowed`;
  } else {
    return `${baseClass} border-slate-800 cursor-pointer hover:bg-slate-800 hover:border-slate-600`;
  }
};

// 计算设置按钮样式
// const getSettingsButtonClass = () => {
//   const baseClass =
//     "flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors";
//   return props.isRunning
//     ? `${baseClass} cursor-not-allowed opacity-50 text-slate-500`
//     : `${baseClass} hover:bg-slate-700 cursor-pointer text-slate-400 hover:text-white`;
// };

// 计算帮助按钮样式
const helpButtonClass =
  "flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors hover:bg-slate-700 cursor-pointer text-slate-400 hover:text-white";

// 获取状态图标
const getStatusIcon = () => {
  const iconClass = "h-4 w-4";
  const status = getScriptStatus();

  switch (status) {
    case "running":
      return {
        component: Loader2,
        class: `${iconClass} animate-spin text-blue-500`,
      };
    case "completed":
      return {
        component: CheckCircle2,
        class: `${iconClass} text-green-500`,
      };
    case "error":
      return {
        component: Circle,
        class: `${iconClass} text-red-500`,
      };
    default:
      return {
        component: Circle,
        class: `${iconClass} text-slate-500`,
      };
  }
};

// 事件处理
const handleCardClick = () => {
  if (props.isRunning) return;
  emit("toggle", props.script.id);
};

// const handleSettings = () => {
//   if (props.isRunning) return;
//   emit("settings", props.script.id);
// };

const handleHelp = () => {
  emit("help", props.script.id);
};
</script>

<style scoped>
/* 正在运行的脚本卡片动画效果 - 边框内部旋转指示条 */
.running-card {
  @apply relative overflow-hidden border-2 border-blue-500/30 bg-gradient-to-br from-slate-800/95 to-slate-700/95;
}

/* 确保卡片内容在指示条之上 */
.running-card > div {
  @apply relative z-20;
  background: inherit;
}
</style>
