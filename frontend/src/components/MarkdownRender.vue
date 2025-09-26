<template>
  <div
    class="markdown-content"
    v-html="renderedContent"
    @click="handleImageClick"
  ></div>

  <!-- 图片放大弹窗 -->
  <Modal
    v-model:visible="showImageModal"
    :show-header="false"
    :show-footer="false"
    size="full"
    @close="closeImageModal"
  >
    <div
      class="flex items-center justify-center min-h-screen bg-black bg-opacity-90"
      @click="closeImageModal"
    >
      <div
        class="relative max-w-[90vw] max-h-[90vh] flex items-center justify-center"
        @click.stop
      >
        <!-- 上一张按钮 -->
        <button
          v-if="imageList.length > 1"
          @click="previousImage"
          class="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white rounded-full p-3 transition-colors z-10"
        >
          <ChevronLeft class="h-6 w-6" />
        </button>

        <!-- 关闭按钮 - 固定在右上角 -->
        <button
          @click="closeImageModal"
          class="absolute top-4 right-4 bg-black bg-opacity-50 hover:bg-opacity-70 text-white rounded-full p-2 transition-colors z-20"
        >
          <X class="h-6 w-6" />
        </button>

        <!-- 图片容器 -->
        <div class="relative">
          <img
            :src="selectedImageSrc"
            :alt="selectedImageAlt"
            class="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
          />

          <!-- 图片计数器 -->
          <div
            v-if="imageList.length > 1"
            class="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
          >
            {{ currentImageIndex + 1 }} / {{ imageList.length }}
          </div>
        </div>

        <!-- 下一张按钮 -->
        <button
          v-if="imageList.length > 1"
          @click="nextImage"
          class="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white rounded-full p-3 transition-colors z-10"
        >
          <ChevronRight class="h-6 w-6" />
        </button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, nextTick } from "vue";
import MarkdownIt from "markdown-it";
import Modal from "./Modal.vue";
import { X, ChevronLeft, ChevronRight } from "lucide-vue-next";

interface Props {
  content: string;
  options?: object;
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  options: () => ({
    html: true,
    linkify: true,
    typographer: true,
    breaks: true,
    xhtmlOut: false,
  }),
});

// 创建 markdown-it 实例
const md = new MarkdownIt(props.options);

// 图片放大弹窗状态
const showImageModal = ref(false);
const selectedImageSrc = ref("");
const selectedImageAlt = ref("");
const imageList = ref<Array<{ src: string; alt: string }>>([]);
const currentImageIndex = ref(0);

// 计算渲染后的内容
const renderedContent = computed(() => {
  if (!props.content) return "";
  const rendered = md.render(props.content);

  // 在内容渲染后收集所有图片
  nextTick(() => {
    collectImages();
  });

  return rendered;
});

// 收集所有图片信息
const collectImages = () => {
  const images = document.querySelectorAll(".markdown-content img");
  imageList.value = Array.from(images).map((img) => ({
    src: (img as HTMLImageElement).src,
    alt: (img as HTMLImageElement).alt || "",
  }));
};

// 处理图片点击事件
const handleImageClick = (event: Event) => {
  const target = event.target as HTMLElement;
  if (target.tagName === "IMG") {
    const img = target as HTMLImageElement;
    const clickedIndex = imageList.value.findIndex(
      (image) => image.src === img.src
    );

    if (clickedIndex !== -1) {
      currentImageIndex.value = clickedIndex;
      selectedImageSrc.value = img.src;
      selectedImageAlt.value = img.alt || "";
      showImageModal.value = true;
    }
  }
};

// 上一张图片
const previousImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--;
  } else {
    currentImageIndex.value = imageList.value.length - 1;
  }
  updateCurrentImage();
};

// 下一张图片
const nextImage = () => {
  if (currentImageIndex.value < imageList.value.length - 1) {
    currentImageIndex.value++;
  } else {
    currentImageIndex.value = 0;
  }
  updateCurrentImage();
};

// 更新当前显示的图片
const updateCurrentImage = () => {
  const currentImage = imageList.value[currentImageIndex.value];
  if (currentImage) {
    selectedImageSrc.value = currentImage.src;
    selectedImageAlt.value = currentImage.alt;
  }
};

// 关闭图片弹窗
const closeImageModal = () => {
  showImageModal.value = false;
  selectedImageSrc.value = "";
  selectedImageAlt.value = "";
  currentImageIndex.value = 0;
};

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  if (!showImageModal.value) return;

  switch (event.key) {
    case "ArrowLeft":
      event.preventDefault();
      previousImage();
      break;
    case "ArrowRight":
      event.preventDefault();
      nextImage();
      break;
    case "Escape":
      event.preventDefault();
      closeImageModal();
      break;
  }
};

// 监听键盘事件
if (typeof window !== "undefined") {
  window.addEventListener("keydown", handleKeydown);
}
</script>

<style scoped>
.markdown-content {
  @apply text-slate-700 dark:text-slate-300 leading-relaxed;
}

/* 标题样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply text-slate-900 dark:text-white font-semibold mb-2 mt-4;
}

.markdown-content :deep(h1) {
  @apply text-xl;
}

.markdown-content :deep(h2) {
  @apply text-lg;
}

.markdown-content :deep(h3) {
  @apply text-base;
}

/* 段落样式 */
.markdown-content :deep(p) {
  @apply text-slate-700 dark:text-slate-300 leading-relaxed mb-3;
}

/* 代码样式 */
.markdown-content :deep(code) {
  @apply bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 px-1.5 py-0.5 rounded text-sm font-mono;
}

.markdown-content :deep(pre) {
  @apply bg-slate-100 dark:bg-slate-800 rounded-lg p-4 overflow-x-auto mb-4;
}

.markdown-content :deep(pre code) {
  @apply bg-transparent p-0 text-sm;
}

/* 列表样式 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply text-slate-700 dark:text-slate-300 space-y-2 mb-4 pl-6;
}

.markdown-content :deep(ul) {
  @apply list-disc;
}

.markdown-content :deep(ol) {
  @apply list-decimal;
}

.markdown-content :deep(li) {
  @apply text-slate-700 dark:text-slate-300 leading-relaxed;
}

.markdown-content :deep(li p) {
  @apply mb-2;
}

/* 链接样式 */
.markdown-content :deep(a) {
  @apply text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
  @apply border-l-4 border-slate-300 dark:border-slate-600 pl-4 italic text-slate-600 dark:text-slate-400 my-4;
}

/* 表格样式 */
.markdown-content :deep(table) {
  @apply w-full border-collapse border border-slate-300 dark:border-slate-700 mb-4;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-slate-300 dark:border-slate-700 px-3 py-2 text-left;
}

.markdown-content :deep(th) {
  @apply bg-slate-100 dark:bg-slate-800 font-semibold text-slate-900 dark:text-white;
}

/* 分割线样式 */
.markdown-content :deep(hr) {
  @apply border-slate-300 dark:border-slate-700 my-6;
}

/* 强调样式 */
.markdown-content :deep(strong) {
  @apply font-semibold text-slate-900 dark:text-white;
}

.markdown-content :deep(em) {
  @apply italic;
}

/* 图片样式 */
.markdown-content :deep(img) {
  @apply cursor-zoom-in rounded-lg shadow-lg;
  max-width: 100%;
  height: auto;
}
</style>
