<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import MarkdownIt from "markdown-it";

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
  }),
});

// 创建 markdown-it 实例
const md = new MarkdownIt(props.options);

// 计算渲染后的内容
const renderedContent = computed(() => {
  if (!props.content) return "";
  return md.render(props.content);
});
</script>

<style scoped>
.markdown-content {
  @apply text-slate-300 leading-relaxed;
}

/* 标题样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply text-white font-semibold mb-2 mt-4;
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
  @apply text-slate-300 leading-relaxed mb-3;
}

/* 代码样式 */
.markdown-content :deep(code) {
  @apply bg-slate-800 text-slate-200 px-1.5 py-0.5 rounded text-sm font-mono;
}

.markdown-content :deep(pre) {
  @apply bg-slate-800 rounded-lg p-4 overflow-x-auto mb-4;
}

.markdown-content :deep(pre code) {
  @apply bg-transparent p-0 text-sm;
}

/* 列表样式 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply text-slate-300 space-y-1 mb-3;
}

.markdown-content :deep(li) {
  @apply text-slate-300;
}

/* 链接样式 */
.markdown-content :deep(a) {
  @apply text-blue-400 hover:text-blue-300 underline;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
  @apply border-l-4 border-slate-600 pl-4 italic text-slate-400 my-4;
}

/* 表格样式 */
.markdown-content :deep(table) {
  @apply w-full border-collapse border border-slate-700 mb-4;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-slate-700 px-3 py-2 text-left;
}

.markdown-content :deep(th) {
  @apply bg-slate-800 font-semibold text-white;
}

/* 分割线样式 */
.markdown-content :deep(hr) {
  @apply border-slate-700 my-6;
}

/* 强调样式 */
.markdown-content :deep(strong) {
  @apply font-semibold text-white;
}

.markdown-content :deep(em) {
  @apply italic;
}
</style>
