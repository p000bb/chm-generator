<template>
  <div class="bg-slate-900 border border-slate-800 rounded-lg">
    <div class="p-4 pb-3">
      <h3
        class="text-lg font-semibold text-white flex items-center justify-between gap-2"
      >
        <div class="flex items-center gap-2">
          <FolderOpen class="h-5 w-5 text-blue-500" />
          输入源文件夹
        </div>
        <span
          v-if="inputFolder"
          class="text-xs px-2 py-1 rounded"
          :class="
            isFolderValid ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          "
        >
          {{ isFolderValid ? "校验通过" : "校验失败" }}
        </span>
      </h3>
    </div>
    <div class="px-4 pb-4">
      <FileSelect
        v-model="inputFolder"
        type="folder"
        placeholder="选择包含源文档的文件夹..."
        :disabled="props.disabled"
        @update:modelValue="onInputFolderChange"
      />
    </div>

    <!-- 芯片配置区域 - 可收缩展开 -->
    <div v-if="inputFolder && isFolderValid" class="border-t border-slate-800">
      <!-- 收缩/展开按钮 -->
      <div class="p-4 pb-4">
        <button
          @click="toggleChipConfig"
          class="flex items-center justify-between w-full text-left hover:bg-slate-800 rounded-md p-2 -m-2 transition-colors"
        >
          <div class="flex items-center gap-2">
            <Cpu class="h-4 w-4 text-purple-500" />
            <span class="text-sm font-medium text-slate-300">芯片配置</span>
            <span class="text-xs text-slate-500"
              >({{ chipConfig.chipName ? "已配置" : "未配置" }})</span
            >
          </div>
          <ChevronDown
            :class="[
              'h-4 w-4 text-slate-400 transition-transform duration-200',
              isChipConfigExpanded ? 'rotate-180' : '',
            ]"
          />
        </button>
      </div>

      <!-- 芯片配置表单 - 可收缩内容 -->
      <div
        v-show="isChipConfigExpanded"
        class="px-4 pb-4 space-y-4 animate-in slide-in-from-top-2 duration-200"
      >
        <!-- 配置参考级联选择器 -->
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">
            <Cpu class="h-4 w-4 inline mr-1" />
            配置参考
          </label>
          <div class="space-y-2">
            <!-- 第一级选择器 -->
            <div class="relative">
              <select
                v-model="selectedCategory"
                @change="onCategoryChange"
                :disabled="props.disabled"
                :class="[
                  'w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 pl-10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none',
                  props.disabled
                    ? 'cursor-not-allowed opacity-50'
                    : 'cursor-pointer',
                ]"
              >
                <option value="" disabled>选择芯片系列...</option>
                <option
                  v-for="category in chipConfigJson"
                  :key="category.name"
                  :value="category.name"
                >
                  {{ category.name }}
                </option>
              </select>
              <Cpu
                class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400"
              />
              <ChevronDown
                class="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
              />
            </div>

            <!-- 第二级选择器 -->
            <div v-if="selectedCategory" class="relative">
              <select
                v-model="selectedChipReference"
                @change="onChipReferenceChange"
                :disabled="props.disabled"
                :class="[
                  'w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 pl-10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none',
                  props.disabled
                    ? 'cursor-not-allowed opacity-50'
                    : 'cursor-pointer',
                ]"
              >
                <option value="" disabled>选择具体芯片...</option>
                <option
                  v-for="chip in currentChipOptions"
                  :key="chip.name"
                  :value="chip.name"
                >
                  {{ chip.name }}
                </option>
              </select>
              <Cpu
                class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400"
              />
              <ChevronDown
                class="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
              />
            </div>
          </div>
        </div>

        <!-- 配置项列表循环 -->
        <div v-for="configItem in chipConfigItems" :key="configItem.key">
          <label class="block text-sm font-medium text-slate-300 mb-2">
            <div class="flex items-center gap-2">
              <component :is="configItem.icon" class="h-4 w-4" />
              <span>{{ configItem.label }}</span>
              <span v-if="configItem.required" class="text-red-500">*</span>
              <div v-if="configItem.description" class="relative group">
                <HelpCircle
                  class="h-4 w-4 text-slate-400 hover:text-slate-300 cursor-help transition-colors"
                />
                <div
                  class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 border border-slate-600"
                >
                  {{ configItem.description }}
                  <div
                    class="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"
                  ></div>
                </div>
              </div>
            </div>
          </label>
          <div class="relative">
            <input
              v-model="chipConfig[configItem.key]"
              :type="configItem.type"
              :placeholder="configItem.placeholder"
              :disabled="props.disabled"
              @blur="onFieldBlur(configItem.key)"
              :class="[
                'w-full bg-slate-800 border rounded-md px-3 py-2 pl-10 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:border-transparent',
                fieldBlurred[configItem.key] &&
                !getFieldValidationStatus(configItem).isValid
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-slate-700 focus:ring-purple-500',
                props.disabled ? 'cursor-not-allowed opacity-50' : '',
              ]"
            />
            <component
              :is="configItem.icon"
              class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400"
            />
            <button
              v-if="chipConfig[configItem.key] && !props.disabled"
              @click="chipConfig[configItem.key] = ''"
              class="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-slate-700 rounded transition-colors"
            >
              <X class="h-3 w-3 text-slate-400 hover:text-white" />
            </button>
          </div>
          <!-- 错误提示 -->
          <div
            v-if="
              fieldBlurred[configItem.key] &&
              !getFieldValidationStatus(configItem).isValid
            "
            class="mt-1 text-sm text-red-500 flex items-center gap-1"
          >
            <X class="h-3 w-3" />
            {{ getFieldValidationStatus(configItem).message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  FolderOpen,
  Cpu,
  Layers,
  Globe,
  Folder,
  ChevronDown,
  X,
  HelpCircle,
} from "lucide-vue-next";
import { ref, computed } from "vue";
import FileSelect from "@/components/FileSelect.vue";
import { message } from "@/utils/message";
import chipConfigJson from "@config/chip.json";
// TODO: 删除模拟数据 - 开发环境测试用
import { mock } from "@/demos/mock";

// 定义类型
interface ChipConfigItem {
  key: keyof ChipConfig;
  label: string;
  type: string;
  placeholder: string;
  icon: any;
  required?: boolean;
  description?: string;
}

interface ChipConfig {
  chipName: string;
  chipVersion: string;
  Cn_WebUrl: string;
  En_WebUrl: string;
  Zip_Url: string;
}

// 定义 props 和 emits
interface Props {
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

const emit = defineEmits<{
  "update:inputFolder": [value: string];
  "update:chipConfig": [value: ChipConfig];
}>();

// TODO: 删除模拟数据 - 开发环境测试用
// 输入文件夹 - 使用模拟数据
const inputFolder = ref(mock.inputFolder);

// TODO: 删除模拟数据 - 开发环境测试用
// 芯片配置 - 使用模拟数据
const chipConfig = ref<ChipConfig>({
  chipName: mock.chipConfig.chipName,
  chipVersion: mock.chipConfig.chipVersion,
  Cn_WebUrl: mock.chipConfig.Cn_WebUrl,
  En_WebUrl: mock.chipConfig.En_WebUrl || "",
  Zip_Url: mock.chipConfig.Zip_Url,
});

// 收缩展开状态
const isChipConfigExpanded = ref(false);

// 必需的文件夹列表（后续可以配置）
const requiredFolders = ref<string[]>(["1-Product_Brief", "2-Datasheet"]);

// TODO: 删除模拟数据 - 开发环境测试用
// 文件夹校验状态 - 模拟数据默认校验通过
const isFolderValid = ref(true);

// 选中的芯片系列
const selectedCategory = ref("");

// 选中的芯片参考
const selectedChipReference = ref("");

// 字段失焦状态跟踪
const fieldBlurred = ref<Record<string, boolean>>({});

// 当前系列下的芯片选项
const currentChipOptions = computed(() => {
  if (!selectedCategory.value) return [];

  const category = chipConfigJson.find(
    (cat: any) => cat.name === selectedCategory.value
  );

  if (category && category.children && Array.isArray(category.children)) {
    return category.children.map((chip: any) => ({
      name: chip.name,
      data: chip,
    }));
  }

  return [];
});

// 芯片配置项数组
const chipConfigItems = ref<ChipConfigItem[]>([
  {
    key: "chipName",
    label: "芯片名称",
    type: "text",
    placeholder: "例如：N32G432X",
    icon: Cpu,
    required: true,
    description: "芯片的完整型号名称，用于文档生成和识别",
  },
  {
    key: "chipVersion",
    label: "芯片版本",
    type: "text",
    placeholder: "例如：2.4.0",
    icon: Layers,
    required: true,
    description: "芯片的版本号，格式为数字和小数点，如：2.4.0",
  },
  {
    key: "Cn_WebUrl",
    label: "中文官网",
    type: "url",
    placeholder:
      "例如：https://www.nationstech.com/product/general/n32g/n32g43x/n32g432",
    icon: Globe,
    required: true,
    description: "芯片的中文官网链接，用于生成文档中的参考链接",
  },
  {
    key: "En_WebUrl",
    label: "英文官网",
    type: "url",
    placeholder: "例如：https://nsing.com.sg/product/General/cortexm4/N32G432",
    icon: Globe,
    required: false,
    description: "芯片的英文官网链接（可选），用于生成多语言文档",
  },
  {
    key: "Zip_Url",
    label: "资源路径",
    type: "text",
    placeholder:
      "例如：https://www.nationstech.com/uploads/zip/175643963044688.zip",
    icon: Folder,
    required: true,
    description: "芯片相关资源的下载链接，如数据手册、应用笔记等",
  },
]);

// 计算是否有芯片配置
const hasChipConfig = computed(() => {
  return Object.values(chipConfig.value).some((value) => value.trim() !== "");
});

// 计算必填字段是否都已填写
const isRequiredFieldsValid = computed(() => {
  const requiredFields = chipConfigItems.value.filter((item) => item.required);
  return requiredFields.every((item) => {
    const validation = getFieldValidationStatus(item);
    return validation.isValid;
  });
});

// 字段验证规则
const fieldValidationRules = {
  chipName: (value: string) => {
    if (!value || value.trim() === "") {
      return { isValid: false, message: "芯片名称为必填项" };
    }
    return { isValid: true, message: "" };
  },
  chipVersion: (value: string) => {
    if (!value || value.trim() === "") {
      return { isValid: false, message: "芯片版本为必填项" };
    }
    // 验证版本号格式：只能包含数字和小数点，小数点不能在开头和结尾
    const versionRegex = /^\d+(\.\d+)*$/;
    if (!versionRegex.test(value)) {
      return {
        isValid: false,
        message: "芯片版本格式不正确，只能包含数字和小数点，如：2.4.0",
      };
    }
    return { isValid: true, message: "" };
  },
  Cn_WebUrl: (value: string) => {
    if (!value || value.trim() === "") {
      return { isValid: false, message: "中文官网为必填项" };
    }
    // 验证URL格式
    const urlRegex = /^https?:\/\/.+/;
    if (!urlRegex.test(value)) {
      return {
        isValid: false,
        message: "请输入有效的中文官网地址，如：https://www.example.com",
      };
    }
    return { isValid: true, message: "" };
  },
  En_WebUrl: (value: string) => {
    if (!value || value.trim() === "") {
      return { isValid: true, message: "" }; // 英文官网为可选字段
    }
    // 验证URL格式
    const urlRegex = /^https?:\/\/.+/;
    if (!urlRegex.test(value)) {
      return {
        isValid: false,
        message: "请输入有效的英文官网地址，如：https://www.example.com",
      };
    }
    return { isValid: true, message: "" };
  },
  Zip_Url: (value: string) => {
    if (!value || value.trim() === "") {
      return { isValid: false, message: "资源路径为必填项" };
    }
    // 验证URL格式
    const urlRegex = /^https?:\/\/.+/;
    if (!urlRegex.test(value)) {
      return {
        isValid: false,
        message:
          "请输入有效的资源路径地址，如：https://www.example.com/file.zip",
      };
    }
    return { isValid: true, message: "" };
  },
};

// 计算必填字段的校验状态
const getFieldValidationStatus = (configItem: ChipConfigItem) => {
  const value = chipConfig.value[configItem.key];
  const rule =
    fieldValidationRules[configItem.key as keyof typeof fieldValidationRules];

  if (!rule) {
    return { isValid: true, message: "" };
  }

  return rule(value);
};

// 校验文件夹内容
const validateFolder = async (folderPath: string) => {
  try {
    // 如果必需文件夹列表为空，跳过校验
    if (requiredFolders.value.length === 0) {
      isFolderValid.value = true;
      return true;
    }

    // 读取文件夹内容
    const result = await window.electronAPI.readDirectory(folderPath);

    if (!result.success) {
      message.error("文件夹校验失败");
      isFolderValid.value = false;
      return false;
    }

    // 检查是否包含所有必需的文件夹
    const actualFolders = result.folders;
    const missingFolders = requiredFolders.value.filter(
      (requiredFolder) => !actualFolders.includes(requiredFolder)
    );

    if (missingFolders.length > 0) {
      message.error("文件夹校验失败");
      isFolderValid.value = false;
      return false;
    }

    // 校验通过
    isFolderValid.value = true;
    return true;
  } catch (error) {
    console.error("文件夹校验失败:", error);
    message.error("文件夹校验失败");
    isFolderValid.value = false;
    return false;
  }
};

// 输入文件夹变化时的处理
const onInputFolderChange = async (value: string) => {
  inputFolder.value = value;
  emit("update:inputFolder", value);

  if (value) {
    // 校验文件夹内容
    await validateFolder(value);
  } else {
    // 清空芯片配置
    chipConfig.value = {
      chipName: "",
      chipVersion: "",
      Cn_WebUrl: "",
      En_WebUrl: "",
      Zip_Url: "",
    };
    isChipConfigExpanded.value = false;
    isFolderValid.value = false;
  }

  // 发送芯片配置更新
  emit("update:chipConfig", chipConfig.value);
};

// 切换芯片配置展开状态
const toggleChipConfig = () => {
  isChipConfigExpanded.value = !isChipConfigExpanded.value;
};

// 监听芯片配置变化
const onChipConfigChange = () => {
  emit("update:chipConfig", chipConfig.value);
};

// 选择芯片系列时的处理
const onCategoryChange = () => {
  // 清空芯片选择
  selectedChipReference.value = "";
  // 清空配置数据
  chipConfig.value = {
    chipName: "",
    chipVersion: "",
    Cn_WebUrl: "",
    En_WebUrl: "",
    Zip_Url: "",
  };
  emit("update:chipConfig", chipConfig.value);
};

// 选择芯片参考时的处理
const onChipReferenceChange = () => {
  const selectedChip = currentChipOptions.value.find(
    (chip) => chip.name === selectedChipReference.value
  );

  if (selectedChip && selectedChip.data) {
    const chipData = selectedChip.data;

    // 自动填充配置数据
    chipConfig.value = {
      chipName: chipData.name || "",
      chipVersion: chipData.chipVersion || "",
      Cn_WebUrl: chipData.Cn_WebUrl || "",
      En_WebUrl: chipData.En_WebUrl || "",
      Zip_Url: chipData.Zip_Url || "",
    };

    // 发送更新
    emit("update:chipConfig", chipConfig.value);
  }
};

// 字段失焦处理
const onFieldBlur = (fieldKey: string) => {
  fieldBlurred.value[fieldKey] = true;
};

// TODO: 删除模拟数据 - 开发环境测试用
// 初始化时发送模拟数据
emit("update:inputFolder", inputFolder.value);
emit("update:chipConfig", chipConfig.value);

// TODO: 删除模拟数据 - 开发环境测试用
// 初始化时设置所有字段为已失焦状态，触发验证
const initializeFieldBlurred = () => {
  chipConfigItems.value.forEach((item) => {
    fieldBlurred.value[item.key] = true;
  });
};

// TODO: 删除模拟数据 - 开发环境测试用
// 在组件挂载后初始化
initializeFieldBlurred();

// 暴露给父组件的方法
defineExpose({
  inputFolder,
  chipConfig,
  hasChipConfig,
  isFolderValid,
  requiredFolders,
  validateFolder,
  chipConfigItems,
  selectedCategory,
  selectedChipReference,
  currentChipOptions,
  isRequiredFieldsValid,
  getFieldValidationStatus,
  fieldBlurred,
  onFieldBlur,
});
</script>

<style></style>
