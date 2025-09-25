<template>
  <div class="space-y-6">
    <!-- 根据选择的类型显示对应的组件 -->
    <GroupScripts
      v-if="activeScriptType === 'group'"
      ref="groupScriptsRef"
      :can-run="props.canRun"
      :is-running="props.isRunning"
      :current-script-index="props.currentScriptIndex"
      :script-results="props.scriptResults"
      :on-cancel-execution="props.onCancelExecution"
      :active-script-type="activeScriptType"
      @run-scripts="handleRunScripts"
      @script-type-change="handleScriptTypeChange"
    />

    <SingleScripts
      v-if="activeScriptType === 'single'"
      ref="singleScriptsRef"
      :can-run="props.canRun"
      :is-running="props.isRunning"
      :current-script-index="props.currentScriptIndex"
      :script-results="props.scriptResults"
      :on-cancel-execution="props.onCancelExecution"
      :active-script-type="activeScriptType"
      @run-scripts="handleRunScripts"
      @script-type-change="handleScriptTypeChange"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import GroupScripts from "./GroupScripts.vue";
import SingleScripts from "./SingleScripts.vue";

// 定义 props
interface Props {
  canRun?: boolean;
  isRunning?: boolean;
  currentScriptIndex?: number;
  scriptResults?: Record<
    string,
    { success: boolean; output: string; error?: string; code: number }
  >;
  onCancelExecution?: () => Promise<{ success: boolean; error?: string }>;
}

const props = withDefaults(defineProps<Props>(), {
  canRun: false,
  isRunning: false,
  currentScriptIndex: -1,
  scriptResults: () => ({}),
});

// 定义 emits
const emit = defineEmits<{
  "run-scripts": [config: any];
}>();

// 脚本类型切换状态
const activeScriptType = ref<"group" | "single">("group");

// 子组件引用
const groupScriptsRef = ref();
const singleScriptsRef = ref();

// 切换脚本类型
const handleScriptTypeChange = (type: "group" | "single") => {
  if (props.isRunning) {
    return; // 运行期间不允许切换
  }

  // 清除另一个类型的选择状态
  if (type === "group") {
    // 清除单独脚本的选择
    if (singleScriptsRef.value && singleScriptsRef.value.scriptsRef) {
      singleScriptsRef.value.scriptsRef.forEach((script: any) => {
        script.checked = false;
      });
    }
  } else {
    // 清除组合脚本的选择
    if (groupScriptsRef.value && groupScriptsRef.value.scriptsRef) {
      groupScriptsRef.value.scriptsRef.forEach((script: any) => {
        script.checked = false;
      });
    }
  }

  activeScriptType.value = type;
};

// 处理脚本执行事件
const handleRunScripts = (configData: any) => {
  emit("run-scripts", configData);
};

// 暴露给父组件的方法
defineExpose({
  handleScriptTypeChange,
  activeScriptType,
});
</script>

<style scoped>
/* 容器组件样式 */
</style>
