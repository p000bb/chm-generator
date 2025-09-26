<template>
  <Transition
    enter-active-class="transition ease-out duration-300"
    enter-from-class="transform opacity-0 scale-95"
    enter-to-class="transform opacity-100 scale-100"
    leave-active-class="transition ease-in duration-200"
    leave-from-class="transform opacity-100 scale-100"
    leave-to-class="transform opacity-0 scale-95"
  >
    <div
      v-if="visible"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="handleOverlayClick"
    >
      <!-- 背景遮罩 -->
      <div
        class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
      ></div>

      <!-- 对话框容器 -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div
          class="relative w-full max-w-md transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-xl transition-all"
        >
          <!-- 对话框头部 -->
          <div
            class="px-6 py-4 border-b border-slate-200 dark:border-slate-700"
          >
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <AlertTriangle
                  v-if="type === 'warning'"
                  class="h-6 w-6 text-yellow-500 dark:text-yellow-400"
                />
                <AlertCircle
                  v-else-if="type === 'error'"
                  class="h-6 w-6 text-red-500 dark:text-red-400"
                />
                <Info
                  v-else-if="type === 'info'"
                  class="h-6 w-6 text-blue-500 dark:text-blue-400"
                />
                <HelpCircle
                  v-else
                  class="h-6 w-6 text-blue-500 dark:text-cyan-400"
                />
              </div>
              <div class="ml-3">
                <h3 class="text-lg font-medium text-slate-900 dark:text-white">
                  {{ title }}
                </h3>
              </div>
            </div>
          </div>

          <!-- 对话框内容 -->
          <div class="px-6 py-4">
            <p
              class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed"
            >
              {{ message }}
            </p>
          </div>

          <!-- 对话框底部按钮 -->
          <div class="px-6 py-4 flex justify-end space-x-3">
            <button
              v-if="showCancel"
              @click="handleCancel"
              class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 hover:text-slate-800 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-cyan-500 transition-colors"
            >
              {{ cancelText }}
            </button>
            <button
              @click="handleConfirm"
              :class="[
                'inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors',
                type === 'error'
                  ? 'bg-red-500 dark:bg-red-600 hover:bg-red-600 dark:hover:bg-red-700'
                  : 'bg-blue-500 dark:bg-cyan-600 hover:bg-blue-600 dark:hover:bg-cyan-700',
              ]"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { AlertTriangle, AlertCircle, Info, HelpCircle } from "lucide-vue-next";

//#region 类型定义
export type ConfirmType = "warning" | "error" | "info" | "question";

export interface ConfirmOptions {
  title?: string;
  message: string;
  type?: ConfirmType;
  confirmText?: string;
  cancelText?: string;
  showCancel?: boolean;
  closeOnOverlay?: boolean;
}

interface ConfirmInstance {
  close: () => void;
}
//#endregion

//#region 组件配置
const props = withDefaults(defineProps<ConfirmOptions>(), {
  title: "确认操作",
  type: "question",
  confirmText: "确认",
  cancelText: "取消",
  showCancel: true,
  closeOnOverlay: false,
});

const emit = defineEmits<{
  confirm: [];
  cancel: [];
  close: [];
}>();
//#endregion

//#region 响应式数据
const visible = ref(false);
//#endregion

//#region 方法
const handleConfirm = () => {
  visible.value = false;
  emit("confirm");
  // 延迟移除DOM元素
  setTimeout(() => {
    emit("close");
  }, 200);
};

const handleCancel = () => {
  visible.value = false;
  emit("cancel");
  // 延迟移除DOM元素
  setTimeout(() => {
    emit("close");
  }, 200);
};

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    handleCancel();
  }
};

const show = () => {
  visible.value = true;
};
//#endregion

//#region 生命周期
onMounted(() => {
  show();
});
//#endregion

// 暴露方法给父组件
defineExpose<ConfirmInstance>({
  close: handleCancel,
});
</script>
