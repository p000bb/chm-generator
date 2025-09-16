<template>
  <div class="space-y-6">
    <!-- 控制按钮区域 -->
    <div class="bg-slate-900 border border-slate-800 rounded-lg">
      <div class="p-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button
              @click="handleSelectAll"
              class="flex items-center gap-2 px-4 py-2 bg-transparent border border-slate-700 hover:bg-slate-800 text-white rounded-md transition-colors"
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
        </div>
        <div v-if="props.isRunning" class="mt-4">
          <div
            class="flex items-center justify-between text-sm text-slate-400 mb-2"
          >
            <span>执行进度</span>
            <span>{{ Math.round(progress) }}%</span>
          </div>
          <div class="w-full bg-slate-800 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: progress + '%' }"
            ></div>
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
          'bg-slate-900 border border-slate-800 rounded-lg relative cursor-pointer transition-colors',
          props.isRunning
            ? 'cursor-not-allowed opacity-50'
            : 'hover:bg-slate-800',
        ]"
      >
        <div class="p-4 pb-3">
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
                :is="getStatusIcon(script.status).component"
                :class="getStatusIcon(script.status).class"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { CheckCircle2, Loader2, Play, Circle } from "lucide-vue-next";
import { ref, computed } from "vue";

// 定义 props
interface Props {
  canRun?: boolean;
  isRunning?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  canRun: false,
  isRunning: false,
});

// 定义 emits
const emit = defineEmits<{
  "run-scripts": [config: any];
}>();

// 脚本数据
const scripts = ref([
  {
    id: "1",
    name: "docs_decompression",
    description: "自动解压所选源文件一级目录下面的zip包",
    checked: true,
    status: "idle",
  },
  {
    id: "2",
    name: "docs_gen_main_html",
    description: "生成主HTML文件",
    checked: true,
    status: "idle",
  },
  {
    id: "3",
    name: "generate_modules",
    description: "生成模块文档",
    checked: true,
    status: "idle",
  },
  {
    id: "4",
    name: "get_chip_data",
    description: "获取芯片数据并生成overview.md",
    checked: true,
    status: "idle",
  },
  {
    id: "5",
    name: "translate_main_modules",
    description: "翻译主模块Markdown文件",
    checked: true,
    status: "idle",
  },
  {
    id: "6",
    name: "docs_main_doxygen",
    description: "主Doxygen文档生成",
    checked: true,
    status: "idle",
  },
  {
    id: "7",
    name: "docs_gen_doxyfile",
    description: "生成Doxyfile配置",
    checked: true,
    status: "idle",
  },
  {
    id: "8",
    name: "docs_gen_doxygen",
    description: "生成Doxygen文档",
    checked: true,
    status: "idle",
  },
  {
    id: "9",
    name: "docs_gen_pdfhtml",
    description: "生成PDF HTML文件",
    checked: true,
    status: "idle",
  },
  {
    id: "10",
    name: "docs_gen_config",
    description: "生成配置文件",
    checked: true,
    status: "idle",
  },
  {
    id: "11",
    name: "docs_gen_examples",
    description: "生成示例文档",
    checked: true,
    status: "idle",
  },
  {
    id: "12",
    name: "docs_gen_examples_overview",
    description: "生成示例概览",
    checked: true,
    status: "idle",
  },
  {
    id: "13",
    name: "docs_gen_examples_description",
    description: "生成示例描述",
    checked: true,
    status: "idle",
  },
  {
    id: "14",
    name: "docs_gen_template_hhc",
    description: "生成HHC模板",
    checked: true,
    status: "idle",
  },
  {
    id: "15",
    name: "docs_gen_hhc",
    description: "生成HHC文件",
    checked: true,
    status: "idle",
  },
  {
    id: "16",
    name: "docs_gen_hhp",
    description: "生成HHP文件",
    checked: true,
    status: "idle",
  },
]);

// 进度条状态（由父组件管理，这里只是显示）
const progress = ref(0);

// 事件处理函数
const handleSelectAll = () => {
  const allSelected = scripts.value.every((script) => script.checked);
  scripts.value.forEach((script) => {
    script.checked = !allSelected;
  });
};

const handleRunSelected = async () => {
  if (!props.canRun) {
    alert("请检查输入源文件夹校验、芯片配置校验和输出目标文件夹是否完整！");
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
  const script = scripts.value.find((script) => script.id === id);
  if (script) {
    script.checked = !script.checked;
  }
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
        class: `${iconClass} text-cyan-500`,
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
  progress,
  handleSelectAll,
  handleRunSelected,
  handleScriptToggle,
});
</script>

<style></style>
