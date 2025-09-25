<template>
  <div class="space-y-4">
    <div class="bg-slate-900 border border-slate-800 rounded-lg">
      <!-- 脚本类型切换 -->
      <div class="p-6 pb-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <!-- 脚本类型切换 -->
            <div class="flex bg-slate-800 rounded-lg p-1">
              <button
                @click="handleScriptTypeChange('group')"
                :disabled="props.isRunning"
                :class="[
                  'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                  activeScriptType === 'group'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white',
                ]"
              >
                组合脚本
              </button>
              <button
                @click="handleScriptTypeChange('single')"
                :disabled="props.isRunning"
                :class="[
                  'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                  activeScriptType === 'single'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white',
                ]"
              >
                单独脚本
              </button>
            </div>

            <span class="text-sm text-slate-400">
              {{ getScriptTypeDescription() }}
            </span>
          </div>
        </div>
      </div>
      <!-- 控制按钮区域 -->
      <div class="p-6 pt-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button
              @click="handleSelectAll"
              :disabled="props.isRunning"
              :class="selectAllButtonClass"
            >
              <CheckCircle2 class="h-4 w-4" />
              {{ selectAllButtonText }}
            </button>
            <span class="text-sm text-slate-400">
              已选择 {{ selectedCount }} / {{ totalCount }} 个{{
                scriptTypeName
              }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="handleRunSelected"
              :disabled="runButtonDisabled"
              class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-md transition-colors"
            >
              <Loader2 v-if="props.isRunning" class="h-4 w-4 animate-spin" />
              <Play v-else class="h-4 w-4" />
              {{ runButtonText }}
            </button>

            <button
              v-if="props.isRunning"
              @click="handleCancelExecution"
              class="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            >
              <X class="h-4 w-4" />
              取消执行
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { CheckCircle2, Loader2, Play, X } from "lucide-vue-next";
import { computed, ref } from "vue";

// 定义 props
interface Props {
  canRun?: boolean;
  isRunning?: boolean;
  selectedCount: number;
  totalCount: number;
  scriptTypeName: string; // "组合脚本" 或 "单独脚本"
  allSelected: boolean; // 是否全选状态
  activeScriptType?: "group" | "single"; // 当前激活的脚本类型
}

const props = withDefaults(defineProps<Props>(), {
  canRun: false,
  isRunning: false,
  selectedCount: 0,
  totalCount: 0,
  scriptTypeName: "脚本",
  allSelected: false,
  activeScriptType: "group",
});

// 定义 emits
const emit = defineEmits<{
  "select-all": [];
  "run-selected": [];
  "cancel-execution": [];
  "script-type-change": [type: "group" | "single"];
}>();

// 内部状态
const activeScriptType = ref<"group" | "single">(props.activeScriptType);

// 计算属性
const selectAllButtonText = computed(() => {
  return props.allSelected ? "取消全选" : "全选脚本";
});

const selectAllButtonClass = computed(() => {
  const baseClass =
    "flex items-center gap-2 px-4 py-2 bg-transparent border border-slate-700 text-white rounded-md transition-colors";
  return props.isRunning
    ? `${baseClass} cursor-not-allowed opacity-50`
    : `${baseClass} hover:bg-slate-800`;
});

const runButtonDisabled = computed(() => {
  return props.isRunning || props.selectedCount === 0 || !props.canRun;
});

const runButtonText = computed(() => {
  return props.isRunning ? "执行中..." : "运行选中脚本";
});

// 获取脚本类型描述
const getScriptTypeDescription = () => {
  if (activeScriptType.value === "group") {
    return "组合脚本：包含多个相关脚本的完整流程";
  } else {
    return "单独脚本：独立的单个脚本功能";
  }
};

// 事件处理
const handleScriptTypeChange = (type: "group" | "single") => {
  if (props.isRunning) return; // 运行期间不允许切换

  activeScriptType.value = type;
  emit("script-type-change", type);
};

const handleSelectAll = () => {
  if (props.isRunning) return;
  emit("select-all");
};

const handleRunSelected = async () => {
  if (!props.canRun) {
    // 使用桌面通知替代 alert
    const { showTaskCompleteNotification, requestNotificationPermission } =
      await import("@/utils/notification");
    await requestNotificationPermission();
    showTaskCompleteNotification("配置检查", false);
    return;
  }
  emit("run-selected");
};

const handleCancelExecution = async () => {
  emit("cancel-execution");
};
</script>
