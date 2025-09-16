<template>
  <div class="flex gap-2">
    <div class="flex-1 relative">
      <input
        :value="modelValue"
        :placeholder="placeholder"
        readonly
        :disabled="disabled"
        :class="[
          'w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 pr-8 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
        ]"
        @click="!disabled && openDialog()"
      />
      <!-- 清空按钮 -->
      <button
        v-if="modelValue && clearable && !disabled"
        @click="clearValue"
        class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-slate-700 rounded transition-colors"
        :title="'清空'"
      >
        <X class="h-3 w-3 text-slate-400 hover:text-white" />
      </button>
    </div>
    <button
      @click="!disabled && openDialog()"
      :disabled="disabled"
      :class="[
        'bg-slate-800 border border-slate-700 p-2 rounded-md transition-colors',
        disabled ? 'cursor-not-allowed opacity-50' : 'hover:bg-slate-700',
      ]"
      :title="buttonTitle"
    >
      <component :is="icon" class="h-4 w-4 text-slate-400" />
    </button>
  </div>
</template>

<script lang="ts" setup>
import { FolderOpen, FileText, X } from "lucide-vue-next";
import { computed } from "vue";

interface Props {
  modelValue: string;
  type?: "file" | "folder";
  placeholder?: string;
  accept?: string; // 文件类型过滤，如 ".txt,.md,.pdf"
  clearable?: boolean; // 是否可清空
  disabled?: boolean; // 是否禁用
}

const props = withDefaults(defineProps<Props>(), {
  type: "folder",
  placeholder: "请选择...",
  accept: "*",
  clearable: true,
  disabled: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const icon = computed(() => {
  return props.type === "file" ? FileText : FolderOpen;
});

const buttonTitle = computed(() => {
  return props.type === "file" ? "选择文件" : "选择文件夹";
});

const clearValue = () => {
  emit("update:modelValue", "");
};

const openDialog = async () => {
  try {
    if (props.type === "file") {
      // 选择文件
      const result = await window.electronAPI.selectFile({
        filters: [
          {
            name: "所有文件",
            extensions:
              props.accept === "*"
                ? ["*"]
                : props.accept.split(",").map((ext) => ext.replace(".", "")),
          },
        ],
      });

      if (result && !result.canceled && result.filePaths.length > 0) {
        emit("update:modelValue", result.filePaths[0]);
      }
    } else {
      // 选择文件夹
      const result = await window.electronAPI.selectFolder();

      if (result && !result.canceled && result.filePaths.length > 0) {
        emit("update:modelValue", result.filePaths[0]);
      }
    }
  } catch (error) {
    console.error("选择文件/文件夹失败:", error);
  }
};
</script>

<style scoped></style>
