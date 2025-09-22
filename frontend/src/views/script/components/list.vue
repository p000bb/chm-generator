<template>
  <div class="space-y-6">
    <!-- 控制按钮区域 -->
    <div class="bg-slate-900 border border-slate-800 rounded-lg">
      <div class="p-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button
              @click="handleSelectAll"
              :disabled="props.isRunning"
              :class="[
                'flex items-center gap-2 px-4 py-2 bg-transparent border border-slate-700 text-white rounded-md transition-colors',
                props.isRunning
                  ? 'cursor-not-allowed opacity-50'
                  : 'hover:bg-slate-800',
              ]"
            >
              <CheckCircle2 class="h-4 w-4" />
              {{
                scripts.every((script) => script.checked)
                  ? "取消全选"
                  : "全选脚本"
              }}
            </button>
            <span class="text-sm text-slate-400">
              已选择 {{ scripts.filter((script) => script.checked).length }} /
              {{ scripts.length }} 个脚本
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="handleRunSelected"
              :disabled="
                props.isRunning ||
                scripts.filter((script) => script.checked).length === 0 ||
                !props.canRun
              "
              class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-md transition-colors"
            >
              <Loader2 v-if="props.isRunning" class="h-4 w-4 animate-spin" />
              <Play v-else class="h-4 w-4" />
              {{ props.isRunning ? "执行中..." : "运行选中脚本" }}
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

    <!-- 脚本卡片网格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="script in scripts"
        :key="script.id"
        @click="handleScriptToggle(script.id)"
        :class="[
          'bg-slate-900 border border-slate-800 rounded-lg relative transition-colors group',
          props.isRunning
            ? 'cursor-not-allowed'
            : 'cursor-pointer hover:bg-slate-800',
        ]"
      >
        <div class="p-4">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                :checked="script.checked"
                @change="handleScriptToggle(script.id)"
                :disabled="props.isRunning"
                class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 rounded focus:ring-blue-500 focus:ring-2 pointer-events-none"
              />
              <div>
                <h4 class="text-base font-semibold text-white">
                  {{ script.name }}
                </h4>
                <p class="text-sm text-slate-400 mt-1">
                  {{ script.description }}
                </p>
              </div>
            </div>
            <!-- 状态图标 -->
            <div class="flex items-center">
              <component
                :is="getStatusIcon(getScriptStatus(script.id)).component"
                :class="getStatusIcon(getScriptStatus(script.id)).class"
              />
            </div>
          </div>
          <!-- 设置和帮助按钮 - 放在卡片下方 -->
          <div
            class="mt-3 pt-3 border-t border-slate-800 group-hover:border-slate-600 transition-colors"
          >
            <div class="flex items-center justify-end gap-2">
              <!-- 设置按钮 -->
              <button
                @click.stop="handleScriptSettings(script.id)"
                :disabled="props.isRunning"
                :class="[
                  'flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors',
                  props.isRunning
                    ? 'cursor-not-allowed opacity-50 text-slate-500'
                    : 'hover:bg-slate-700 cursor-pointer text-slate-400 hover:text-white',
                ]"
                title="脚本设置"
              >
                <Settings class="h-3.5 w-3.5" />
                设置
              </button>
              <!-- 帮助按钮 -->
              <button
                @click.stop="handleScriptHelp(script.id)"
                :class="[
                  'flex items-center gap-2 px-3 py-1.5 text-sm rounded transition-colors',
                  'hover:bg-slate-700 cursor-pointer text-slate-400 hover:text-white',
                ]"
                title="脚本说明"
              >
                <HelpCircle class="h-3.5 w-3.5" />
                说明
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 帮助弹窗 -->
    <Modal
      v-model:visible="showHelpModal"
      :title="`${currentHelpScript} - 脚本说明`"
      size="xl"
      @close="handleCloseHelp"
    >
      <div v-if="helpLoading" class="flex items-center justify-center py-8">
        <Loader2 class="h-8 w-8 animate-spin text-blue-500" />
        <span class="ml-2 text-slate-400">加载中...</span>
      </div>
      <div v-else-if="helpError" class="text-center py-8">
        <Circle class="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p class="text-red-400 mb-4">{{ helpError }}</p>
        <button
          @click="loadHelpContent(currentHelpScript)"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          重试
        </button>
      </div>
      <MarkdownRender v-else :content="helpContent" />
    </Modal>
  </div>
</template>

<script lang="ts" setup>
import {
  CheckCircle2,
  Loader2,
  Play,
  Circle,
  X,
  Settings,
  HelpCircle,
} from "lucide-vue-next";
import { ref, computed } from "vue";
import { confirm } from "@/utils/confirm";
import { message } from "@/utils/message";
import Modal from "@/components/Modal.vue";
import MarkdownRender from "@/components/MarkdownRender.vue";

// 定义 props
interface Props {
  canRun?: boolean;
  isRunning?: boolean;
  currentScriptIndex?: number;
  scriptResults?: Record<
    string,
    { success: boolean; output: string; error?: string; code: number }
  >;
  onCancelExecution?: () => Promise<{ success: boolean; error?: string }>;
}

const props = withDefaults(defineProps<Props>(), {
  canRun: false,
  isRunning: false,
  currentScriptIndex: -1,
  scriptResults: () => ({}),
});

// 定义 emits
const emit = defineEmits<{
  "run-scripts": [config: any];
}>();

// 弹窗状态管理
const showHelpModal = ref(false);
const currentHelpScript = ref("");
const helpContent = ref("");
const helpLoading = ref(false);
const helpError = ref("");

// 脚本数据
const scripts = ref([
  {
    id: "1",
    name: "docs_decompression",
    description: "自动解压所选源文件一级目录下面的zip包",
    checked: false,
    status: "idle",
  },
  {
    id: "2",
    name: "docs_gen_main_html",
    description: "生成主HTML文件",
    checked: false,
    status: "idle",
  },
  {
    id: "3",
    name: "generate_modules",
    description: "生成模块文档",
    checked: false,
    status: "idle",
  },
  {
    id: "4",
    name: "get_chip_data",
    description: "获取芯片数据并生成overview.md",
    checked: false,
    status: "idle",
  },
  {
    id: "5",
    name: "translate_main_modules",
    description: "翻译主模块Markdown文件",
    checked: false,
    status: "idle",
  },
  {
    id: "6",
    name: "docs_main_doxygen",
    description: "主Doxygen文档生成",
    checked: false,
    status: "idle",
  },
  {
    id: "7",
    name: "docs_gen_doxyfile",
    description: "生成Doxyfile配置",
    checked: false,
    status: "idle",
  },
  {
    id: "8",
    name: "docs_gen_doxygen",
    description: "生成Doxygen文档",
    checked: false,
    status: "idle",
  },
  {
    id: "9",
    name: "docs_gen_pdfhtml",
    description: "生成PDF HTML文件",
    checked: false,
    status: "idle",
  },
  {
    id: "10",
    name: "docs_gen_config",
    description: "生成配置文件",
    checked: false,
    status: "idle",
  },
  {
    id: "11",
    name: "docs_gen_examples",
    description: "生成示例文档",
    checked: false,
    status: "idle",
  },
  {
    id: "12",
    name: "docs_gen_examples_overview",
    description: "生成示例概览",
    checked: false,
    status: "idle",
  },
  {
    id: "13",
    name: "docs_gen_examples_description",
    description: "生成示例描述",
    checked: false,
    status: "idle",
  },
  {
    id: "14",
    name: "docs_gen_template_hhc",
    description: "生成HHC模板",
    checked: false,
    status: "idle",
  },
  {
    id: "15",
    name: "docs_gen_hhc",
    description: "生成HHC文件",
    checked: false,
    status: "idle",
  },
  {
    id: "16",
    name: "docs_gen_hhp",
    description: "生成HHP文件",
    checked: false,
    status: "idle",
  },
  {
    id: "17",
    name: "generate_chm_hhc",
    description: "生成chm文件",
    checked: false,
    status: "idle",
  },
]);

// 计算每个脚本的状态
const getScriptStatus = (scriptId: string) => {
  // 获取选中的脚本列表
  const selectedScripts = scripts.value.filter((script) => script.checked);

  // 如果当前正在执行这个脚本（基于选中脚本的索引）
  if (props.currentScriptIndex >= 0) {
    const currentRunningScript = selectedScripts[props.currentScriptIndex];
    if (currentRunningScript && currentRunningScript.id === scriptId) {
      return "running";
    }
  }

  // 如果脚本已经执行完成
  if (props.scriptResults[scriptId]) {
    return props.scriptResults[scriptId].success ? "completed" : "error";
  }

  // 默认状态
  return "idle";
};

// 事件处理函数
const handleSelectAll = () => {
  // 运行期间不允许全选/取消全选
  if (props.isRunning) {
    return;
  }

  const allSelected = scripts.value.every((script) => script.checked);
  scripts.value.forEach((script) => {
    script.checked = !allSelected;
  });
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

  // 准备传递给父组件的数据
  const configData = {
    selectedScripts: scripts.value.filter((script) => script.checked),
  };

  // 发送执行事件给父组件
  emit("run-scripts", configData);
};

const handleScriptToggle = (id: string) => {
  // 运行期间不允许切换脚本选择
  if (props.isRunning) {
    return;
  }

  const script = scripts.value.find((script) => script.id === id);
  if (script) {
    script.checked = !script.checked;
  }
};

const handleCancelExecution = async () => {
  // 显示确认对话框
  const confirmResult = await confirm.warning(
    "确定要取消当前正在执行的脚本吗？",
    "取消执行确认"
  );
  if (!confirmResult.confirmed) {
    return;
  }

  try {
    // 调用父组件传递的取消执行函数
    if (props.onCancelExecution) {
      const result = await props.onCancelExecution();

      if (result && result.success) {
        message.success("脚本执行已成功取消");
      } else {
        message.error(`取消执行失败: ${result?.error || "未知错误"}`);
      }
    } else {
      // 如果没有传递取消执行函数，显示提示
      message.warning("取消执行功能不可用");
    }
  } catch (error) {
    console.error("取消执行时发生错误:", error);
    message.error("取消执行时发生错误");
  }
};

const handleScriptSettings = (scriptId: string) => {
  // 运行期间不允许打开设置
  if (props.isRunning) {
    return;
  }

  // TODO: 实现脚本设置功能
  console.log("打开脚本设置:", scriptId);
  message.info("脚本设置功能开发中...");
};

const handleScriptHelp = async (scriptId: string) => {
  const script = scripts.value.find((s) => s.id === scriptId);
  if (!script) return;

  currentHelpScript.value = script.name;
  showHelpModal.value = true;
  await loadHelpContent(script.name);
};

// 加载帮助内容
const loadHelpContent = async (scriptName: string) => {
  helpLoading.value = true;
  helpError.value = "";
  helpContent.value = "";

  try {
    // 动态导入对应的 md 文件
    const module = await import(`@/helpdoc/${scriptName}.md?raw`);
    helpContent.value = module.default;
  } catch (err) {
    console.error("加载帮助文档失败:", err);
    helpError.value = `未找到 ${scriptName} 的帮助文档`;
  } finally {
    helpLoading.value = false;
  }
};

// 关闭帮助弹窗
const handleCloseHelp = () => {
  showHelpModal.value = false;
  currentHelpScript.value = "";
  helpContent.value = "";
  helpError.value = "";
};

const getStatusIcon = (status: string) => {
  const iconClass = "h-4 w-4";

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

// 暴露给父组件的方法
defineExpose({
  scripts,
  handleSelectAll,
  handleRunSelected,
  handleScriptToggle,
  handleScriptSettings,
  handleScriptHelp,
});
</script>

<style></style>
