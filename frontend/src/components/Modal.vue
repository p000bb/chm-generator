<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 transition-opacity"
      @click="handleBackdropClick"
    >
      <div
        :class="[
          'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl transition-all transform',
          sizeClasses,
          positionClasses,
        ]"
        @click.stop
      >
        <!-- 头部 -->
        <div
          v-if="showHeader"
          class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700"
        >
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">
            {{ title }}
          </h3>
          <button
            v-if="showCloseButton"
            @click="handleClose"
            class="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"
          >
            <X class="h-6 w-6" />
          </button>
        </div>

        <!-- 内容区域 -->
        <div :class="contentClasses">
          <slot />
        </div>

        <!-- 底部按钮 -->
        <div
          v-if="showFooter"
          class="flex items-center justify-end gap-3 p-6 border-t border-slate-200 dark:border-slate-700"
        >
          <slot name="footer">
            <button
              @click="handleClose"
              class="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-white rounded-md transition-colors"
            >
              关闭
            </button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { X } from "lucide-vue-next";

interface Props {
  visible: boolean;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
  showHeader?: boolean;
  showFooter?: boolean;
  showCloseButton?: boolean;
  closeOnBackdrop?: boolean;
  closeOnEscape?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "",
  size: "md",
  showHeader: true,
  showFooter: true,
  showCloseButton: true,
  closeOnBackdrop: true,
  closeOnEscape: true,
});

const emit = defineEmits<{
  close: [];
  "update:visible": [value: boolean];
}>();

// 尺寸类
const sizeClasses = computed(() => {
  const sizeMap = {
    sm: "max-w-sm w-full mx-4",
    md: "max-w-md w-full mx-4",
    lg: "max-w-2xl w-full mx-4",
    xl: "max-w-4xl w-full mx-4",
    "2xl": "max-w-6xl w-full mx-4",
    full: "max-w-[95vw] w-full mx-4",
  };
  return sizeMap[props.size];
});

// 位置类
const positionClasses = computed(() => {
  return "max-h-[90vh] flex flex-col";
});

// 内容区域类
const contentClasses = computed(() => {
  const classes = ["flex-1"];

  if (props.showHeader && props.showFooter) {
    classes.push("overflow-y-auto p-6");
  } else if (props.showHeader) {
    classes.push("overflow-y-auto p-6 pb-0");
  } else if (props.showFooter) {
    classes.push("overflow-y-auto p-6 pt-0");
  } else {
    classes.push("overflow-y-auto p-6");
  }

  return classes.join(" ");
});

const handleClose = () => {
  emit("close");
  emit("update:visible", false);
};

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    handleClose();
  }
};

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  if (props.closeOnEscape && event.key === "Escape") {
    handleClose();
  }
};

// 监听键盘事件
if (typeof window !== "undefined") {
  window.addEventListener("keydown", handleKeydown);
}
</script>

<style scoped>
/* 确保弹框在最顶层 */
.fixed {
  z-index: 9999;
}
</style>
