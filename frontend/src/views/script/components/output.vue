<template>
  <div
    class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg"
  >
    <div class="p-4 pb-3">
      <h3
        class="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2"
      >
        <FileText class="h-5 w-5 text-blue-500 dark:text-cyan-500" />
        输出目标文件夹
      </h3>
    </div>
    <div class="px-4 pb-4">
      <FileSelect
        v-model="outputFolder"
        type="folder"
        placeholder="选择CHM文件输出位置..."
        :disabled="props.disabled"
        @update:modelValue="onOutputFolderChange"
      />
      <div class="mt-3 flex justify-end">
        <button
          @click="openOutputFolder"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-cyan-600 rounded-md hover:bg-blue-700 dark:hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <FolderOpen class="h-4 w-4" />
          打开输出文件夹
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { FileText, FolderOpen } from "lucide-vue-next";
import { ref } from "vue";
import FileSelect from "@/components/FileSelect.vue";
// TODO: 删除模拟数据 - 开发环境测试用
import { mock } from "@/demos/mock";

// 定义 props 和 emits
interface Props {
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

const emit = defineEmits<{
  "update:outputFolder": [value: string];
}>();

// 输出文件夹 - 根据环境使用模拟数据或空值
const outputFolder = ref(mock.outputFolder);

// 输出文件夹变化时的处理
const onOutputFolderChange = (value: string) => {
  outputFolder.value = value;
  emit("update:outputFolder", value);
};

// 打开输出文件夹
const openOutputFolder = async () => {
  if (!outputFolder.value) return;

  try {
    // 使用 Electron API 打开文件夹
    await window.electronAPI.openFolder(outputFolder.value);
  } catch (error) {
    console.error("打开文件夹失败:", error);
  }
};

// 初始化时发送数据（开发环境为模拟数据，生产环境为空值）
emit("update:outputFolder", outputFolder.value);

// 暴露给父组件的方法
defineExpose({
  outputFolder,
});
</script>

<style></style>
