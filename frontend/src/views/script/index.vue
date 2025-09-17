<template>
  <div class="script-page space-y-6">
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
      :current-script-index="currentScriptIndex"
      :script-results="scriptResults"
      @run-scripts="onRunScripts"
      @cancel-execution="onCancelExecution"
    />
  </div>
</template>

<script lang="ts" setup>
defineOptions({
  name: "Script",
});

import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  onActivated,
  onDeactivated,
  toRaw,
} from "vue";
import Entry from "./components/entry.vue";
import Output from "./components/output.vue";
import List from "./components/list.vue";
import {
  showTaskCompleteNotification,
  requestNotificationPermission,
} from "@/utils/notification";

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

// 脚本执行状态管理
const currentScriptIndex = ref(-1);
const scriptResults = ref<
  Record<
    string,
    { success: boolean; output: string; error?: string; code: number }
  >
>({});
const isCancelled = ref(false);

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

// 清空页面日志
const clearPageLogs = async () => {
  try {
    await window.electronAPI.clearRealtimeLog();
    console.log("清空页面日志");
  } catch (error) {
    console.error("清空日志失败:", error);
  }
};

const onCancelExecution = () => {
  isCancelled.value = true;
  console.log("用户请求取消脚本执行");
};

const onRunScripts = async (configData: any) => {
  if (!canRun.value) {
    alert("请检查输入源文件夹校验、芯片配置校验和输出目标文件夹是否完整！");
    return;
  }

  isRunning.value = true;
  currentScriptIndex.value = -1;
  scriptResults.value = {};
  isCancelled.value = false;

  try {
    // 获取当前时刻的非响应式数据快照
    const currentInputFolder = toRaw(inputFolder.value);
    const currentOutputFolder = toRaw(outputFolder.value);
    const currentChipConfig = toRaw(chipConfig.value);

    // 准备完整的配置数据（非响应式）
    const fullConfigData = {
      inputFolder: currentInputFolder,
      outputFolder: currentOutputFolder,
      chipConfig: currentChipConfig,
      ...toRaw(configData),
    };

    // 清空页面日志（在开始执行脚本前清空一次）
    await clearPageLogs();

    // 执行选中的脚本
    const selectedScripts = fullConfigData.selectedScripts || [];

    for (let i = 0; i < selectedScripts.length; i++) {
      // 检查是否被取消
      if (isCancelled.value) {
        console.log("脚本执行已被取消");
        break;
      }

      const script = selectedScripts[i];

      // 更新当前执行脚本索引
      currentScriptIndex.value = i;

      try {
        // 调用 Electron API 执行 Python 脚本
        const result = await window.electronAPI.runPythonScript(
          script.name,
          currentInputFolder,
          currentOutputFolder,
          currentChipConfig
        );

        // 记录脚本执行结果
        scriptResults.value[script.id] = result;

        console.log(`脚本 ${script.name} 执行结果:`, result);
      } catch (error) {
        console.error(`脚本 ${script.name} 执行失败:`, error);

        // 记录失败的脚本结果
        scriptResults.value[script.id] = {
          success: false,
          output: "",
          error: error instanceof Error ? error.message : String(error),
          code: -1,
        };

        // 继续执行下一个脚本（根据需求）
        console.log(`脚本 ${script.name} 执行失败，继续执行下一个脚本...`);
      }
    }

    if (isCancelled.value) {
      console.log("脚本执行已被用户取消");
      // 显示取消通知
      await requestNotificationPermission();
      showTaskCompleteNotification("脚本执行", false);
    } else {
      // 检查是否有脚本执行失败
      const selectedScripts = fullConfigData.selectedScripts || [];
      const failedScripts = selectedScripts.filter((script: any) => {
        const result = scriptResults.value[script.id];
        return result && !result.success;
      });

      if (failedScripts.length > 0) {
        console.log(`有 ${failedScripts.length} 个脚本执行失败`);
        const failedNames = failedScripts
          .map((script: any) => script.name)
          .join("、");
        // 显示失败通知，包含失败的脚本名称
        await requestNotificationPermission();
        showTaskCompleteNotification(`脚本执行失败: ${failedNames}`, false);
      } else {
        console.log("所有脚本执行完成！");
        // 显示完成通知
        await requestNotificationPermission();
        showTaskCompleteNotification("脚本执行", true);
      }
    }
  } catch (error) {
    console.error("执行失败:", error);

    // 显示错误通知
    await requestNotificationPermission();
    showTaskCompleteNotification("脚本执行", false);
  } finally {
    isRunning.value = false;
    currentScriptIndex.value = -1;
    isCancelled.value = false;
  }
};

onMounted(() => {
  console.log("Script 组件挂载");
});

onUnmounted(() => {
  console.log("Script 组件卸载");
});

onActivated(() => {
  console.log("Script 组件激活");
});

onDeactivated(() => {
  console.log("Script 组件停用");
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
