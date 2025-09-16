<template>
  <div
    class="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center relative overflow-hidden"
  >
    <div class="text-center z-10 relative">
      <div class="mb-6">
        <span class="text-8xl inline-block animate-bounce">😵</span>
      </div>

      <h1
        class="text-9xl font-bold text-red-500 dark:text-red-400 mb-4"
        style="text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1)"
      >
        404
      </h1>
      <h2 class="text-3xl font-semibold text-gray-800 dark:text-white mb-4">
        页面未找到
      </h2>
      <p class="text-lg text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto">
        抱歉，您访问的页面不存在或已被移除。
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center mb-12">
        <router-link
          to="/"
          class="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 bg-red-500 hover:bg-red-600 text-white shadow-lg"
        >
          <span class="text-lg">🏠</span>
          返回首页
        </router-link>
        <button
          @click="goBack"
          class="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 bg-gray-500 hover:bg-gray-600 text-white"
        >
          <span class="text-lg">⬅️</span>
          返回上页
        </button>
      </div>

      <div
        class="bg-white dark:bg-gray-700 rounded-lg p-6 shadow-lg max-w-md mx-auto"
      >
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">
          可能需要帮助？
        </h3>
        <div class="flex flex-wrap gap-4 justify-center">
          <a
            href="#"
            class="text-blue-500 hover:text-blue-600 underline transition-colors duration-200"
            >查看文档</a
          >
          <a
            href="#"
            class="text-blue-500 hover:text-blue-600 underline transition-colors duration-200"
            >联系支持</a
          >
          <a
            href="#"
            class="text-blue-500 hover:text-blue-600 underline transition-colors duration-200"
            >报告问题</a
          >
        </div>
      </div>
    </div>

    <div class="absolute inset-0 pointer-events-none">
      <div
        class="absolute text-4xl opacity-20 animate-float"
        v-for="i in 6"
        :key="i"
        :style="{
          animationDelay: `${i * 0.5}s`,
          top:
            i === 1
              ? '10%'
              : i === 2
              ? '20%'
              : i === 3
              ? '60%'
              : i === 4
              ? '70%'
              : i === 5
              ? '40%'
              : '50%',
          left: i === 1 ? '10%' : i === 3 ? '5%' : i === 5 ? '20%' : 'auto',
          right: i === 2 ? '10%' : i === 4 ? '15%' : i === 6 ? '5%' : 'auto',
        }"
      >
        {{ getRandomEmoji() }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1);
  } else {
    router.push("/");
  }
};

const getRandomEmoji = () => {
  const emojis = ["🚀", "💻", "⚡", "🎯", "🌟", "💡", "🔧", "📱"];
  return emojis[Math.floor(Math.random() * emojis.length)];
};
</script>

<style scoped lang="scss">
// 所有样式都使用原子化类名，不再需要 @apply
// 只保留必要的动画和响应式样式
@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.animate-float {
  animation: float 6s ease-in-out infinite;
}
</style>
