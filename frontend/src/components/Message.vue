<template>
  <Transition
    enter-active-class="transition ease-out duration-300"
    enter-from-class="transform opacity-0 translate-y-2"
    enter-to-class="transform opacity-100 translate-y-0"
    leave-active-class="transition ease-in duration-200"
    leave-from-class="transform opacity-100 translate-y-0"
    leave-to-class="transform opacity-0 translate-y-2"
  >
    <div
      v-if="visible"
      :class="[
        'fixed top-4 right-4 z-50 max-w-sm w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg',
        type === 'success' ? 'border-green-500 dark:border-green-500' : '',
        type === 'error' ? 'border-red-500 dark:border-red-500' : '',
        type === 'warning' ? 'border-yellow-500 dark:border-yellow-500' : '',
        type === 'info' ? 'border-blue-500 dark:border-blue-500' : '',
      ]"
    >
      <div class="p-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <CheckCircle
              v-if="type === 'success'"
              class="h-5 w-5 text-green-500 dark:text-green-400"
            />
            <XCircle
              v-else-if="type === 'error'"
              class="h-5 w-5 text-red-500 dark:text-red-400"
            />
            <AlertTriangle
              v-else-if="type === 'warning'"
              class="h-5 w-5 text-yellow-500 dark:text-yellow-400"
            />
            <Info v-else class="h-5 w-5 text-blue-500 dark:text-cyan-400" />
          </div>
          <div class="ml-3 w-0 flex-1">
            <p class="text-sm font-medium text-slate-900 dark:text-white">
              {{ message }}
            </p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button
              @click="close"
              class="bg-slate-100 dark:bg-slate-800 rounded-md inline-flex text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-cyan-500 transition-colors"
            >
              <span class="sr-only">关闭</span>
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-vue-next";

//#region 类型定义
interface Props {
  type: "success" | "error" | "warning" | "info";
  message: string;
  duration?: number;
}

interface MessageInstance {
  close: () => void;
}
//#endregion

//#region 组件配置
const props = withDefaults(defineProps<Props>(), {
  duration: 3000,
});

const emit = defineEmits<{
  close: [];
}>();
//#endregion

//#region 响应式数据
const visible = ref(false);
let timer: NodeJS.Timeout | null = null;
//#endregion

//#region 方法
const close = () => {
  visible.value = false;
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  // 延迟移除DOM元素
  setTimeout(() => {
    emit("close");
  }, 200);
};

const show = () => {
  visible.value = true;
  if (props.duration > 0) {
    timer = setTimeout(() => {
      close();
    }, props.duration);
  }
};
//#endregion

//#region 生命周期
onMounted(() => {
  show();
});

// 暴露方法给父组件
defineExpose<MessageInstance>({
  close,
});
//#endregion
</script>
