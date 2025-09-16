<template>
  <div class="space-y-6">
    <!-- 文件夹选择区域 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- 输入源文件夹和芯片配置 -->
      <Entry
        ref="entryRef"
        :disabled="isRunning"
        @update:input-folder="onInputFolderChange"
        @update:chip-config="onChipConfigChange"
      />

      <!-- 输出目标文件夹 -->
      <Output
        ref="outputRef"
        :disabled="isRunning"
        @update:output-folder="onOutputFolderChange"
      />
    </div>

    <!-- 脚本列表和控制区域 -->
    <List
      ref="listRef"
      :can-run="canRun"
      :is-running="isRunning"
      @run-scripts="onRunScripts"
    />
  </div>
</template>

<script lang="ts" setup>
defineOptions({
  name: "Script",
});

import { ref, computed, onMounted } from "vue";
import Entry from "./components/entry.vue";
import Output from "./components/output.vue";
import List from "./components/list.vue";

// 子组件引用
const entryRef = ref();
const outputRef = ref();
const listRef = ref();

// 状态管理
const inputFolder = ref("");
const outputFolder = ref("");
const chipConfig = ref({
  chipName: "",
  chipVersion: "",
  Cn_WebUrl: "",
  En_WebUrl: "",
  Zip_Url: "",
});
const isRunning = ref(false);

// 计算是否可以运行
const canRun = computed(() => {
  // 检查输入源文件夹校验通过
  const isInputValid = entryRef.value?.isFolderValid || false;

  // 检查芯片配置校验通过
  const isChipConfigValid = entryRef.value?.isRequiredFieldsValid || false;

  // 检查输出目标文件夹有值
  const isOutputValid = !!outputFolder.value;

  return isInputValid && isChipConfigValid && isOutputValid;
});

// 事件处理函数
const onInputFolderChange = (value: string) => {
  inputFolder.value = value;
};

const onOutputFolderChange = (value: string) => {
  outputFolder.value = value;
};

const onChipConfigChange = (value: any) => {
  chipConfig.value = value;
};

const onRunScripts = async (configData: any) => {
  if (!canRun.value) {
    alert("请检查输入源文件夹校验、芯片配置校验和输出目标文件夹是否完整！");
    return;
  }

  isRunning.value = true;

  try {
    // 准备完整的配置数据
    const fullConfigData = {
      inputFolder: inputFolder.value,
      outputFolder: outputFolder.value,
      chipConfig: chipConfig.value,
      ...configData,
    };

    console.log("执行配置:", fullConfigData);

    // 这里可以调用 Python 脚本
    // const result = await window.electronAPI.runPythonScript(fullConfigData);

    // 模拟执行过程
    console.log("开始执行脚本...");

    // 模拟执行时间
    await new Promise((resolve) => setTimeout(resolve, 3000));

    alert("脚本执行完成！");
  } catch (error) {
    console.error("执行失败:", error);
    alert(
      `执行失败: ${error instanceof Error ? error.message : String(error)}`
    );
  } finally {
    isRunning.value = false;
  }
};

onMounted(() => {
  console.log("Script 组件挂载");
});

// 暴露给父组件的方法
defineExpose({
  inputFolder,
  outputFolder,
  chipConfig,
  canRun,
});
</script>

<style></style>
