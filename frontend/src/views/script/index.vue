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
      :on-cancel-execution="handleCancelExecution"
      @run-scripts="onRunScripts"
    />
  </div>
</template>

<script lang="ts" setup>
defineOptions({
  name: "Script",
});

import { ref, computed, toRaw, nextTick } from "vue";
import Entry from "./components/entry.vue";
import Output from "./components/output.vue";
import List from "./components/list.vue";
import {
  showTaskCompleteNotification,
  requestNotificationPermission,
} from "@/utils/notification";
import { message } from "@/utils/message";

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
    {
      success: boolean;
      output: string;
      error?: string;
      code: number;
      subScripts?: Array<{
        name: string;
        success: boolean;
        output: string;
        error?: string;
        code: number;
      }>;
    }
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
  } catch (error) {
    message.warning(`清空日志失败:${error}`);
  }
};

const onCancelExecution = async () => {
  try {
    // 调用主进程API终止Python进程
    const result = await window.electronAPI.cancelPythonScript();

    if (result?.success) {
      isCancelled.value = true;

      // 立即停止执行循环
      isRunning.value = false;
      currentScriptIndex.value = -1;

      return { success: true };
    } else {
      console.error("取消脚本执行失败:", result?.error);
      // 即使API调用失败，也设置取消标志
      isCancelled.value = true;

      return { success: false, error: result?.error || "未知错误" };
    }
  } catch (error) {
    console.error("取消脚本执行时发生错误:", error);
    // 即使发生错误，也设置取消标志
    isCancelled.value = true;

    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
};

// 处理取消执行事件，并返回结果给子组件
const handleCancelExecution = async () => {
  const result = await onCancelExecution();
  return result;
};

const onRunScripts = async (configData: any) => {
  if (!canRun.value) {
    message.error(
      "请检查输入源文件夹校验、芯片配置校验和输出目标文件夹是否完整！"
    );
    return;
  }

  isRunning.value = true;
  currentScriptIndex.value = -1; // 初始化为 -1
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

    // 在循环开始前设置第一个脚本的索引，确保第一个脚本的动画能显示
    if (selectedScripts.length > 0) {
      currentScriptIndex.value = 0;
      await nextTick(); // 等待响应式更新完成
    }

    for (let i = 0; i < selectedScripts.length; i++) {
      // 检查是否被取消
      if (isCancelled.value) {
        break;
      }

      const script = selectedScripts[i];

      // 更新当前执行脚本索引（选中的脚本索引）
      // 第一个脚本的索引已经在循环开始前设置了，这里只需要更新后续脚本的索引
      if (i > 0) {
        currentScriptIndex.value = i;
      }

      // 等待响应式更新完成
      await nextTick();

      // 判断是组合脚本还是单独脚本
      if (script.scripts && script.scripts.length > 0) {
        // 组合脚本：按顺序执行scripts数组中的每个脚本
        const groupScriptKey = `group_${script.id}`;

        for (let j = 0; j < script.scripts.length; j++) {
          // 检查是否被取消
          if (isCancelled.value) {
            break;
          }

          const subScriptName = script.scripts[j];

          try {
            // 再次检查是否被取消（在调用API前）
            if (isCancelled.value) {
              break;
            }

            // 调用 Electron API 执行 Python 脚本
            const result = await window.electronAPI.runPythonScript(
              subScriptName,
              currentInputFolder,
              currentOutputFolder,
              currentChipConfig
            );

            // 检查是否在脚本执行期间被取消
            if (isCancelled.value) {
              break;
            }

            // 记录子脚本执行结果（使用组合脚本的ID作为key，但记录子脚本的结果）
            if (!scriptResults.value[groupScriptKey]) {
              scriptResults.value[groupScriptKey] = {
                success: true,
                output: "",
                subScripts: [],
                code: 0,
              };
            }

            // 添加子脚本结果
            scriptResults.value[groupScriptKey].subScripts!.push({
              name: subScriptName,
              success: result.success,
              output: result.output,
              error: result.error,
              code: result.code,
            });

            // 如果子脚本失败，标记整个组合脚本为失败
            if (!result.success) {
              scriptResults.value[groupScriptKey].success = false;
              scriptResults.value[
                groupScriptKey
              ].error = `子脚本 ${subScriptName} 执行失败: ${result.error}`;
            }
          } catch (error) {
            console.error(`子脚本 ${subScriptName} 执行失败:`, error);

            // 检查是否被取消
            if (isCancelled.value) {
              break;
            }

            // 记录失败的子脚本结果
            if (!scriptResults.value[groupScriptKey]) {
              scriptResults.value[groupScriptKey] = {
                success: false,
                output: "",
                subScripts: [],
                code: -1,
              };
            }

            scriptResults.value[groupScriptKey].subScripts!.push({
              name: subScriptName,
              success: false,
              output: "",
              error: error instanceof Error ? error.message : String(error),
              code: -1,
            });

            scriptResults.value[groupScriptKey].success = false;
            scriptResults.value[
              groupScriptKey
            ].error = `子脚本 ${subScriptName} 执行失败: ${
              error instanceof Error ? error.message : String(error)
            }`;

            // 继续执行下一个子脚本
          }
        }
      } else {
        // 单独脚本：直接执行

        try {
          // 再次检查是否被取消（在调用API前）
          if (isCancelled.value) {
            break;
          }

          // 调用 Electron API 执行 Python 脚本
          const result = await window.electronAPI.runPythonScript(
            script.name,
            currentInputFolder,
            currentOutputFolder,
            currentChipConfig
          );

          // 检查是否在脚本执行期间被取消
          if (isCancelled.value) {
            break;
          }

          // 记录脚本执行结果（使用单独脚本的命名空间）
          const singleScriptKey = `single_${script.id}`;
          scriptResults.value[singleScriptKey] = result;
        } catch (error) {
          console.error(`脚本 ${script.name} 执行失败:`, error);

          // 检查是否被取消
          if (isCancelled.value) {
            break;
          }

          // 记录失败的脚本结果
          const singleScriptKey = `single_${script.id}`;
          scriptResults.value[singleScriptKey] = {
            success: false,
            output: "",
            error: error instanceof Error ? error.message : String(error),
            code: -1,
          };

          // 继续执行下一个脚本（根据需求）
        }
      }
    }

    if (isCancelled.value) {
      // 脚本执行已取消，不显示桌面通知
    } else {
      // 检查是否有脚本执行失败
      const selectedScripts = fullConfigData.selectedScripts || [];
      const failedScripts = [];

      // 检查所有选中的脚本结果
      for (const script of selectedScripts) {
        const scriptKey =
          script.scripts && script.scripts.length > 0
            ? `group_${script.id}`
            : `single_${script.id}`;

        const result = scriptResults.value[scriptKey];
        if (result && !result.success) {
          failedScripts.push(script);
        }
      }

      if (failedScripts.length > 0) {
        const failedNames = failedScripts
          .map((script: any) => script.name)
          .join("、");
        // 显示失败通知，包含失败的脚本名称
        await requestNotificationPermission();
        showTaskCompleteNotification(false, failedNames);
      } else {
        // 显示完成通知
        await requestNotificationPermission();
        showTaskCompleteNotification(true);
      }
    }
  } catch (error) {
    console.error("执行失败:", error);

    // 显示错误通知
    await requestNotificationPermission();
    showTaskCompleteNotification(false);
  } finally {
    isRunning.value = false;
    currentScriptIndex.value = -1;
    isCancelled.value = false;
  }
};

// 暴露给父组件的方法
defineExpose({
  inputFolder,
  outputFolder,
  chipConfig,
  canRun,
});
</script>

<style></style>
