<template>
  <div class="space-y-6">
    <!-- 控制按钮区域 -->
    <ScriptControls
      :can-run="props.canRun"
      :is-running="isRunning"
      :selected-count="selectedCount"
      :total-count="totalCount"
      :script-type-name="'单独脚本'"
      :all-selected="allSelected"
      :active-script-type="props.activeScriptType"
      @select-all="handleSelectAll"
      @run-selected="handleRunSelected"
      @cancel-execution="handleCancelExecutionWrapper"
      @script-type-change="handleScriptTypeChange"
    />

    <!-- 单独脚本卡片网格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <ScriptCard
        v-for="script in scriptsRef"
        :key="script.id"
        :script="script"
        :is-running="isRunning"
        :current-script-index="currentScriptIndex"
        :is-current-executing="isCurrentExecuting(script.id)"
        :script-results="scriptResults"
        :show-script-count="false"
        @toggle="handleScriptToggle"
        @settings="handleScriptSettings"
        @help="handleScriptHelp"
      />
    </div>

    <!-- 帮助弹窗 - 单独脚本不显示tabs -->
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
import { ref, computed } from "vue";
import { Loader2, Circle } from "lucide-vue-next";
import Modal from "@/components/Modal.vue";
import MarkdownRender from "@/components/MarkdownRender.vue";
import ScriptCard from "./ScriptCard.vue";
import ScriptControls from "./ScriptControls.vue";
import {
  useScriptState,
  type SingleScript,
} from "../composables/useScriptState";

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
  activeScriptType?: "group" | "single";
}

const props = withDefaults(defineProps<Props>(), {
  canRun: false,
  isRunning: false,
  currentScriptIndex: -1,
  scriptResults: () => ({}),
  activeScriptType: "single",
});

// 定义 emits
const emit = defineEmits<{
  "run-scripts": [config: any];
  "script-type-change": [type: "group" | "single"];
}>();

// 单独脚本数据
const singleScriptsData: SingleScript[] = [
  {
    id: "1",
    name: "docs_decompression",
    description: "自动解压所选源文件一级目录下面的zip包(每次执行覆盖解压)",
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
];

// 使用父组件传递的状态
const isRunning = computed(() => props.isRunning);
const currentScriptIndex = computed(() => props.currentScriptIndex || -1);

// 使用脚本状态管理
const {
  scriptsRef,
  selectedScripts,
  selectedCount,
  totalCount,
  allSelected,
  handleSelectAll,
  handleScriptToggle,
  handleCancelExecution,
  handleScriptSettings,
} = useScriptState(singleScriptsData, isRunning, currentScriptIndex);

// 使用父组件传递的 scriptResults
const scriptResults = computed(() => props.scriptResults);

// 判断是否是当前正在执行的脚本
const isCurrentExecuting = (scriptId: string) => {
  // 如果没有运行，直接返回false
  if (!isRunning.value) {
    return false;
  }

  // 如果currentScriptIndex为-1，说明还没有开始执行任何脚本
  // 但如果是第一个选中的脚本，应该显示为正在执行
  if (currentScriptIndex.value < 0) {
    const firstSelectedScript = selectedScripts.value[0];
    return firstSelectedScript && firstSelectedScript.id === scriptId;
  }

  // 正常情况：检查当前索引对应的脚本
  const currentScript = selectedScripts.value[currentScriptIndex.value];
  return currentScript && currentScript.id === scriptId;
};

// 弹窗状态管理
const showHelpModal = ref(false);
const currentHelpScript = ref("");
const helpContent = ref("");
const helpLoading = ref(false);
const helpError = ref("");

// 处理脚本类型切换
const handleScriptTypeChange = (type: "group" | "single") => {
  emit("script-type-change", type);
};

// 运行选中脚本
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
    selectedScripts: selectedScripts.value,
  };

  // 发送执行事件给父组件
  emit("run-scripts", configData);
};

// 处理取消执行
const handleCancelExecutionWrapper = async () => {
  if (props.onCancelExecution) {
    await handleCancelExecution(props.onCancelExecution);
  }
};

const handleScriptHelp = async (scriptId: string) => {
  const script = scriptsRef.value.find((s) => s.id === scriptId);
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

// 暴露给父组件的方法
defineExpose({
  scriptsRef,
  handleSelectAll,
  handleRunSelected,
  handleScriptToggle,
  handleScriptSettings,
  handleScriptHelp,
});
</script>

<style scoped>
/* 单独脚本组件样式 */
</style>
