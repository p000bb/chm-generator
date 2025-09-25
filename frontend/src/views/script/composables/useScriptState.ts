import { computed, ref, type Ref } from "vue";

import { confirm } from "@/utils/confirm";
import { message } from "@/utils/message";

// 脚本基础接口
export interface BaseScript {
  id: string;
  name: string;
  description: string;
  checked: boolean;
  status: string;
}

// 组合脚本接口
export interface GroupScript extends BaseScript {
  scripts: string[];
  time: number;
}

// 单独脚本接口
export interface SingleScript extends BaseScript {}

// 子脚本结果接口（用于组合脚本）
export interface SubScriptResult {
  name: string;
  success: boolean;
  output: string;
  error?: string;
  code: number;
}

// 脚本结果接口
export interface ScriptResult {
  success: boolean;
  output: string;
  error?: string;
  code: number;
  subScripts?: SubScriptResult[]; // 组合脚本的子脚本结果
}

// 脚本状态管理 composable
export function useScriptState<T extends BaseScript>(
  scripts: T[],
  externalIsRunning?: Ref<boolean>,
  externalCurrentScriptIndex?: Ref<number>
) {
  const scriptsRef = ref(scripts);
  const isRunning = externalIsRunning || ref(false);
  const currentScriptIndex = externalCurrentScriptIndex || ref(-1);
  const scriptResults = ref<Record<string, ScriptResult>>({});
  const isCancelled = ref(false);

  // 计算属性
  const selectedScripts = computed(() =>
    scriptsRef.value.filter((script) => script.checked)
  );

  const selectedCount = computed(() => selectedScripts.value.length);

  const totalCount = computed(() => scriptsRef.value.length);

  const allSelected = computed(() =>
    scriptsRef.value.every((script) => script.checked)
  );

  const canRun = computed(() => selectedCount.value > 0 && !isRunning.value);

  // 脚本状态计算
  const getScriptStatus = (scriptId: string) => {
    // 如果脚本已经执行完成
    if (scriptResults.value[scriptId]) {
      const result = scriptResults.value[scriptId];

      // 如果是组合脚本，检查是否有子脚本结果
      if (result.subScripts && result.subScripts.length > 0) {
        // 组合脚本：检查所有子脚本是否都成功
        const allSubScriptsSuccess = result.subScripts.every(
          (sub: any) => sub.success
        );
        return allSubScriptsSuccess ? "completed" : "error";
      } else {
        // 单独脚本：直接检查成功状态
        return result.success ? "completed" : "error";
      }
    }

    // 如果当前正在执行这个脚本
    if (isRunning.value && currentScriptIndex.value >= 0) {
      const currentRunningScript =
        selectedScripts.value[currentScriptIndex.value];
      if (currentRunningScript && currentRunningScript.id === scriptId) {
        return "running";
      }
    }

    // 默认状态
    return "idle";
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    if (isRunning.value) return;

    const allSelectedValue = allSelected.value;
    scriptsRef.value.forEach((script) => {
      script.checked = !allSelectedValue;
    });
  };

  // 切换脚本选择
  const handleScriptToggle = (id: string) => {
    if (isRunning.value) return;

    const script = scriptsRef.value.find((script) => script.id === id);
    if (script) {
      script.checked = !script.checked;
    }
  };

  // 取消执行
  const handleCancelExecution = async (
    onCancelExecution?: () => Promise<{ success: boolean; error?: string }>
  ) => {
    if (!isRunning.value) {
      message.warning("当前没有正在执行的脚本");
      return;
    }

    const confirmResult = await confirm.warning(
      "确定要取消当前正在执行的脚本吗？",
      "取消执行确认"
    );
    if (!confirmResult.confirmed) {
      return;
    }

    try {
      if (onCancelExecution) {
        const result = await onCancelExecution();

        if (result && result.success) {
          message.success("脚本执行已成功取消");
        } else {
          message.error(`取消执行失败: ${result?.error || "未知错误"}`);
        }
      } else {
        message.warning("取消执行功能不可用");
      }
    } catch (error) {
      console.error("取消执行时发生错误:", error);
      message.error("取消执行时发生错误");
    }
  };

  // 脚本设置
  const handleScriptSettings = (scriptId: string) => {
    if (isRunning.value) return;
    console.log("打开脚本设置:", scriptId);
    message.info("脚本设置功能开发中...");
  };

  // 重置状态
  const resetState = () => {
    isRunning.value = false;
    currentScriptIndex.value = -1;
    scriptResults.value = {};
    isCancelled.value = false;
  };

  // 开始执行
  const startExecution = () => {
    isRunning.value = true;
    currentScriptIndex.value = -1;
    scriptResults.value = {};
    isCancelled.value = false;
  };

  // 结束执行
  const endExecution = () => {
    isRunning.value = false;
    currentScriptIndex.value = -1;
    isCancelled.value = false;
  };

  return {
    // 状态
    scriptsRef,
    isRunning,
    currentScriptIndex,
    scriptResults,
    isCancelled,

    // 计算属性
    selectedScripts,
    selectedCount,
    totalCount,
    allSelected,
    canRun,

    // 方法
    getScriptStatus,
    handleSelectAll,
    handleScriptToggle,
    handleCancelExecution,
    handleScriptSettings,
    resetState,
    startExecution,
    endExecution,
  };
}
