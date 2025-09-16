<template>
  <div class="bg-slate-900 border border-slate-800 rounded-lg">
    <div class="p-4 pb-3">
      <h3 class="text-lg font-semibold text-white flex items-center gap-2">
        <FileText class="h-5 w-5 text-cyan-500" />
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
    </div>
  </div>
</template>

<script lang="ts" setup>
import { FileText } from "lucide-vue-next";
import { ref } from "vue";
import FileSelect from "@/components/FileSelect.vue";

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

// 输出文件夹
const outputFolder = ref("");

// 输出文件夹变化时的处理
const onOutputFolderChange = (value: string) => {
  outputFolder.value = value;
  emit("update:outputFolder", value);
};

// 暴露给父组件的方法
defineExpose({
  outputFolder,
});
</script>

<style></style>
