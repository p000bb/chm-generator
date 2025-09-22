<template>
  <div class="setting-page space-y-6">
    <!-- 基本配置 -->
    <div class="bg-slate-800 rounded-lg border border-slate-700 shadow-sm">
      <div class="p-6 border-b border-slate-700">
        <h2 class="text-xl font-semibold text-white flex items-center gap-2">
          <Settings class="h-5 w-5 text-cyan-500" />
          基本配置
        </h2>
        <p class="text-sm text-slate-400 mt-1">设置CHM生成工具的基本参数</p>
      </div>
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="field in basicConfigFields"
            :key="field.key"
            class="space-y-2"
          >
            <label :for="field.key" class="text-sm font-medium text-slate-300">
              <div class="flex items-center justify-between gap-2">
                <span>{{ field.label }}</span>
                <div
                  v-if="field.description"
                  class="flex items-center justify-between flex-1"
                >
                  <!-- 悬浮提示按钮 -->
                  <div class="relative group">
                    <HelpCircle
                      class="h-4 w-4 text-slate-400 hover:text-slate-300 cursor-help transition-colors"
                      title="查看提示信息"
                    />
                    <div
                      class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 border border-slate-600"
                    >
                      {{ field.description }}
                      <div
                        class="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"
                      ></div>
                    </div>
                  </div>

                  <!-- 详细说明按钮（根据配置显示） -->
                  <button
                    v-if="field.helpDoc"
                    @click="() => showHelp(field.helpDoc!)"
                    class="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-md border border-slate-600 hover:border-blue-500 transition-all duration-200"
                    title="查看详细操作步骤"
                  >
                    <FileText class="h-3 w-3" />
                    <span>详细说明</span>
                  </button>
                </div>
              </div>
            </label>
            <input
              :id="field.key"
              v-model="basicConfig[field.key]"
              :type="field.type"
              :placeholder="field.placeholder"
              class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 翻译配置 -->
    <div class="bg-slate-800 rounded-lg border border-slate-700 shadow-sm">
      <div class="p-6 border-b border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <h2
              class="text-xl font-semibold text-white flex items-center gap-2"
            >
              <Languages class="h-5 w-5 text-cyan-500" />
              翻译配置
            </h2>
            <p class="text-sm text-slate-400 mt-1">
              管理技术术语的中英文对照表
            </p>
          </div>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <!-- 添加新翻译 -->
        <div
          class="flex gap-2 p-4 bg-slate-700/50 rounded-lg border border-slate-600"
        >
          <input
            v-model="newTranslation.chinese"
            type="text"
            placeholder="专业术语"
            class="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
          />
          <input
            v-model="newTranslation.english"
            type="text"
            placeholder="对照翻译"
            class="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
          />
          <button
            @click="addTranslation"
            class="inline-flex items-center justify-center w-10 h-10 text-white bg-cyan-600 rounded-md hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors"
          >
            <Plus class="w-4 h-4" />
          </button>
        </div>

        <!-- 翻译列表 -->
        <div
          class="h-96 w-full rounded-md border border-slate-600 overflow-y-auto bg-slate-700/30"
        >
          <div class="p-4 space-y-2">
            <div
              v-for="translation in translations"
              :key="translation.id"
              class="flex gap-2 items-center p-2 hover:bg-slate-700/50 rounded border border-slate-600/50"
            >
              <input
                :value="translation.chinese"
                @input="
                  updateTranslation(
                    translation.id,
                    'chinese',
                    ($event.target as HTMLInputElement).value
                  )
                "
                type="text"
                class="flex-1 h-8 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
              />
              <span class="text-slate-400 px-2">→</span>
              <input
                :value="translation.english"
                @input="
                  updateTranslation(
                    translation.id,
                    'english',
                    ($event.target as HTMLInputElement).value
                  )
                "
                type="text"
                class="flex-1 h-8 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
              />
              <button
                @click="removeTranslation(translation.id)"
                class="inline-flex items-center justify-center w-8 h-8 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center text-sm text-slate-400">
          <span>共 {{ translations.length }} 个翻译对</span>
          <button
            @click="saveConfig"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-cyan-600 rounded-md hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors"
          >
            <Save class="w-4 h-4" />
            保存配置
          </button>
        </div>
      </div>
    </div>

    <!-- 帮助弹窗 -->
    <Modal
      v-model:visible="showHelpModal"
      :title="`${currentHelpFieldLabel} - 详细说明`"
      size="xl"
      @close="handleCloseHelp"
    >
      <div v-if="helpLoading" class="flex items-center justify-center py-8">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
        ></div>
        <span class="ml-2 text-slate-400">加载中...</span>
      </div>
      <div v-else-if="helpError" class="text-center py-8">
        <div
          class="h-12 w-12 text-red-500 mx-auto mb-4 flex items-center justify-center"
        >
          <X class="h-8 w-8" />
        </div>
        <p class="text-red-400 mb-4">{{ helpError }}</p>
        <button
          @click="() => loadHelpContent(currentHelpDoc)"
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
import { ref, reactive, onMounted } from "vue";
import {
  Settings,
  Languages,
  Plus,
  Trash2,
  Save,
  HelpCircle,
  FileText,
  X,
} from "lucide-vue-next";
import baseConfig from "@config/base.json";
import { message } from "@/utils/message";
import { confirm } from "@/utils/confirm";
import Modal from "@/components/Modal.vue";
import MarkdownRender from "@/components/MarkdownRender.vue";

defineOptions({
  name: "Setting",
});

// 基本配置字段定义
interface BasicConfigField {
  key: "Base_DownloadUrl" | "Md_DownloadUrl" | "PHPSESSID";
  label: string;
  type: string;
  placeholder: string;
  description?: string;
  helpDoc?: string; // MD 文档文件名（不含扩展名）
}

const basicConfigFields: BasicConfigField[] = [
  {
    key: "Base_DownloadUrl",
    label: "下载地址",
    type: "text",
    placeholder: "请输入下载地址",
    description: "用于下载芯片相关资源的基地址",
  },
  {
    key: "Md_DownloadUrl",
    label: "官网地址",
    type: "text",
    placeholder: "请输入官网地址",
    description: "芯片厂商的官方网站地址，用于生成文档中的参考链接",
  },
  {
    key: "PHPSESSID",
    label: "PHPSESSID",
    type: "text",
    placeholder: "请输入PHPSESSID",
    description: "用于访问需要登录的资源的会话标识符",
    helpDoc: "phpsessid", // 对应 phpsessid.md 文件
  },
];

// 基本配置状态 - 从baseConfig中读取
const basicConfig = reactive({
  Base_DownloadUrl: baseConfig.Base_DownloadUrl || "",
  Md_DownloadUrl: baseConfig.Md_DownloadUrl || "",
  PHPSESSID: baseConfig.PHPSESSID || "",
});

// 翻译配置状态
interface Translation {
  id: number;
  chinese: string;
  english: string;
}

// 从baseConfig中读取技术术语翻译
const translations = ref<Translation[]>(
  Object.entries(baseConfig.Technical_Terms || {}).map(
    ([chinese, english], index) => ({
      id: index + 1,
      chinese,
      english,
    })
  )
);

const newTranslation = reactive({
  chinese: "",
  english: "",
});

// 帮助弹窗状态管理
const showHelpModal = ref(false);
const helpContent = ref("");
const helpLoading = ref(false);
const helpError = ref("");
const currentHelpFieldLabel = ref("");
const currentHelpDoc = ref("");

let nextId = translations.value.length + 1;

// 添加翻译
const addTranslation = () => {
  if (newTranslation.chinese.trim() && newTranslation.english.trim()) {
    // 检查是否已存在相同的专业术语
    const exists = translations.value.some(
      (t) => t.chinese === newTranslation.chinese.trim()
    );

    if (exists) {
      message.warning("该专业术语已存在，请修改后再添加");
      return;
    }

    translations.value.push({
      id: nextId++,
      chinese: newTranslation.chinese.trim(),
      english: newTranslation.english.trim(),
    });
    newTranslation.chinese = "";
    newTranslation.english = "";
    message.success("翻译添加成功");
  } else {
    message.warning("请填写完整的专业术语和对照翻译");
  }
};

// 更新翻译
const updateTranslation = (
  id: number,
  field: "chinese" | "english",
  value: string
) => {
  const translation = translations.value.find((t) => t.id === id);
  if (translation) {
    translation[field] = value;
  }
};

// 删除翻译
const removeTranslation = async (id: number) => {
  const index = translations.value.findIndex((t) => t.id === id);
  if (index > -1) {
    const translation = translations.value[index];

    // 显示确认对话框
    const result = await confirm.delete(
      `确定要删除翻译 "${translation.chinese} → ${translation.english}" 吗？`,
      "删除翻译确认"
    );

    if (!result.confirmed) {
      return;
    }

    translations.value.splice(index, 1);
    message.success(
      `已删除翻译: ${translation.chinese} → ${translation.english}`
    );
  }
};

// 保存配置
const saveConfig = async () => {
  // 显示确认对话框
  const result = await confirm.save(
    "确定要保存当前配置吗？这将覆盖现有的配置文件。",
    "保存配置确认"
  );
  if (!result.confirmed) {
    return;
  }

  try {
    // 构建要保存的配置对象
    const updatedConfig = {
      ...baseConfig,
      Base_DownloadUrl: basicConfig.Base_DownloadUrl,
      Md_DownloadUrl: basicConfig.Md_DownloadUrl,
      PHPSESSID: basicConfig.PHPSESSID,
      Technical_Terms: translations.value.reduce((acc, translation) => {
        acc[translation.chinese] = translation.english;
        return acc;
      }, {} as Record<string, string>),
    };

    // 调用Electron API保存配置
    const result = (await window.electronAPI.saveConfig(updatedConfig)) as {
      success: boolean;
      error?: string;
    };

    if (result.success) {
      console.log("配置保存成功");
      message.success("配置已保存！");
    } else {
      console.error("配置保存失败:", result.error);
      message.error(`配置保存失败: ${result.error || "未知错误"}`);
    }
  } catch (error) {
    console.error("保存配置时发生错误:", error);
    message.error("保存配置时发生错误");
  }
};

// 显示帮助文档
const showHelp = async (helpDoc: string) => {
  // 找到对应的配置项，获取字段标签
  const configItem = basicConfigFields.find((item) => item.helpDoc === helpDoc);
  currentHelpFieldLabel.value = configItem?.label || "帮助";
  currentHelpDoc.value = helpDoc;

  showHelpModal.value = true;
  await loadHelpContent(helpDoc);
};

// 加载帮助内容
const loadHelpContent = async (helpDoc: string) => {
  helpLoading.value = true;
  helpError.value = "";
  helpContent.value = "";

  try {
    // 动态导入对应的 md 文件
    const module = await import(`@/helpdoc/${helpDoc}.md?raw`);
    helpContent.value = module.default;
  } catch (err) {
    console.error("加载帮助文档失败:", err);
    helpError.value = `未找到 ${helpDoc} 的帮助文档`;
  } finally {
    helpLoading.value = false;
  }
};

// 关闭帮助弹窗
const handleCloseHelp = () => {
  showHelpModal.value = false;
  helpContent.value = "";
  helpError.value = "";
  currentHelpFieldLabel.value = "";
  currentHelpDoc.value = "";
};

// 组件挂载时加载配置
onMounted(() => {
  // 这里可以从本地存储或后端加载配置
  console.log("配置页面已加载");
});
</script>

<style scoped>
/* 自定义滚动条样式 - 与日志页面保持一致 */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* 确保页面本身不出现滚动条 */
.h-screen {
  overflow: auto;
}

/* 强制长文本换行 */
.log-message {
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  max-width: 100%;
}
</style>
