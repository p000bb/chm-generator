<template>
  <div class="space-y-6">
    <!-- 控制按钮区域 -->
    <ScriptControls
      :can-run="props.canRun"
      :is-running="isRunning"
      :selected-count="selectedCount"
      :total-count="totalCount"
      :script-type-name="'组合脚本'"
      :all-selected="allSelected"
      :active-script-type="props.activeScriptType"
      @select-all="handleSelectAll"
      @run-selected="handleRunSelected"
      @cancel-execution="handleCancelExecutionWrapper"
      @script-type-change="handleScriptTypeChange"
    />

    <!-- 组合脚本卡片网格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <ScriptCard
        v-for="script in scriptsRef"
        :key="script.id"
        :script="script"
        :is-running="isRunning"
        :current-script-index="currentScriptIndex"
        :is-current-executing="isCurrentExecuting(script.id)"
        :script-results="scriptResults"
        :show-script-count="true"
        @toggle="handleScriptToggle"
        @settings="handleScriptSettings"
        @help="handleScriptHelp"
      />
    </div>

    <!-- 帮助弹窗 - 组合脚本显示tabs -->
    <Modal
      v-model:visible="showHelpModal"
      :title="`${currentHelpApplication?.name || ''} - 脚本说明`"
      size="xl"
      @close="handleCloseHelp"
    >
      <div v-if="helpLoading" class="flex items-center justify-center py-8">
        <Loader2
          class="h-8 w-8 animate-spin text-blue-500 dark:text-blue-500"
        />
        <span class="ml-2 text-slate-600 dark:text-slate-400">加载中...</span>
      </div>
      <div v-else-if="helpError" class="text-center py-8">
        <Circle class="h-12 w-12 text-red-500 dark:text-red-500 mx-auto mb-4" />
        <p class="text-red-600 dark:text-red-400 mb-4">{{ helpError }}</p>
        <button
          @click="loadHelpContent(currentHelpApplication)"
          class="px-4 py-2 bg-blue-600 dark:bg-blue-600 hover:bg-blue-700 dark:hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          重试
        </button>
      </div>
      <div v-else-if="currentHelpApplication">
        <!-- 脚本列表和tabs -->
        <div class="space-y-4">
          <!-- 脚本列表显示 -->
          <div class="bg-slate-100 dark:bg-slate-800 rounded-lg p-4">
            <h4
              class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
            >
              包含的脚本：
            </h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(scriptName, index) in currentHelpApplication.scripts"
                :key="scriptName"
                class="px-2 py-1 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs rounded"
              >
                {{ index + 1 }}. {{ scriptName }}
              </span>
            </div>
          </div>

          <!-- Tabs 导航 -->
          <div class="border-b border-slate-300 dark:border-slate-700">
            <nav
              class="-mb-px flex space-x-8 overflow-x-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800"
            >
              <button
                v-for="scriptName in currentHelpApplication.scripts"
                :key="scriptName"
                @click="handleTabChange(scriptName)"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex-shrink-0',
                  activeHelpTab === scriptName
                    ? 'border-blue-500 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-400',
                ]"
              >
                {{ scriptName }}
              </button>
            </nav>
          </div>

          <!-- Tab 内容 -->
          <div class="min-h-[300px]">
            <div
              v-if="helpContentLoading"
              class="flex items-center justify-center py-8"
            >
              <Loader2 class="h-6 w-6 animate-spin text-blue-500" />
              <span class="ml-2 text-slate-400">加载中...</span>
            </div>
            <div v-else-if="helpContentError" class="text-center py-8">
              <Circle class="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p class="text-red-400 text-sm">{{ helpContentError }}</p>
            </div>
            <MarkdownRender v-else :content="currentHelpContent" />
          </div>
        </div>
      </div>
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
  type GroupScript,
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
  activeScriptType: "group",
});

// 定义 emits
const emit = defineEmits<{
  "run-scripts": [config: any];
  "script-type-change": [type: "group" | "single"];
}>();

// 组合脚本数据
const groupScriptsData: GroupScript[] = [
  {
    id: "1",
    name: "解压源文件",
    description: "覆盖解压所选输入源文件下所有的zip包",
    scripts: ["docs_decompression"],
    checked: false,
    status: "idle",
    time: 1,
  },
  {
    id: "2",
    name: "Overview模块构建",
    description: "生成Overview模块的HTML文件",
    scripts: [
      "docs_gen_main_html",
      "generate_modules",
      "get_chip_data",
      "translate_main_modules",
      "docs_main_doxygen",
      "docs_gen_config",
    ],
    checked: false,
    status: "idle",
    time: 5,
  },
  {
    id: "3",
    name: "子模块构建",
    description: "按照目录结构生成子模块的HTML文件",
    scripts: [
      "docs_gen_doxyfile",
      "docs_gen_doxygen",
      "docs_gen_pdfhtml",
      "docs_gen_examples",
      "docs_gen_examples_overview",
      "docs_gen_examples_description",
    ],
    checked: false,
    status: "idle",
    time: 10,
  },
  {
    id: "4",
    name: "构建chm",
    description: "根据前置脚本生成的文件，生成chm文件",
    scripts: [
      "docs_gen_template_hhc",
      "docs_gen_hhc",
      "docs_gen_hhp",
      "generate_chm_hhc",
    ],
    checked: false,
    status: "idle",
    time: 10,
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
} = useScriptState(groupScriptsData, isRunning, currentScriptIndex);

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
const currentHelpApplication = ref<any>(null);
const activeHelpTab = ref("");
const helpContent = ref("");
const helpLoading = ref(false);
const helpError = ref("");
const helpContentLoading = ref(false);
const helpContentError = ref("");
const currentHelpContent = ref("");

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
    showTaskCompleteNotification(false);
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

  currentHelpApplication.value = script;
  showHelpModal.value = true;

  // 设置默认激活的tab为第一个脚本
  if (script.scripts && script.scripts.length > 0) {
    activeHelpTab.value = script.scripts[0];
    await loadHelpContent(script);
  }
};

// 加载帮助内容
const loadHelpContent = async (application: any) => {
  helpLoading.value = true;
  helpError.value = "";
  helpContent.value = "";

  try {
    if (
      !application ||
      !application.scripts ||
      application.scripts.length === 0
    ) {
      helpError.value = "没有找到脚本信息";
      return;
    }

    // 加载第一个脚本的内容作为默认显示
    await loadScriptHelpContent(application.scripts[0]);
  } catch (err) {
    console.error("加载帮助文档失败:", err);
    helpError.value = `加载帮助文档失败: ${err}`;
  } finally {
    helpLoading.value = false;
  }
};

// 加载单个脚本的帮助内容
const loadScriptHelpContent = async (scriptName: string) => {
  helpContentLoading.value = true;
  helpContentError.value = "";
  currentHelpContent.value = "";

  try {
    // 动态导入对应的 md 文件
    const module = await import(`@/helpdoc/${scriptName}.md?raw`);
    currentHelpContent.value = module.default;
  } catch (err) {
    console.error(`加载脚本 ${scriptName} 帮助文档失败:`, err);
    helpContentError.value = `未找到 ${scriptName} 的帮助文档`;
  } finally {
    helpContentLoading.value = false;
  }
};

// 监听tab切换
const handleTabChange = async (scriptName: string) => {
  activeHelpTab.value = scriptName;
  await loadScriptHelpContent(scriptName);
};

// 关闭帮助弹窗
const handleCloseHelp = () => {
  showHelpModal.value = false;
  currentHelpApplication.value = null;
  activeHelpTab.value = "";
  helpContent.value = "";
  helpError.value = "";
  helpContentLoading.value = false;
  helpContentError.value = "";
  currentHelpContent.value = "";
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
